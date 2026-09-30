"""Capa de negocio — apertura, cancelación e historial de transacciones."""
import asyncio
import logging
from datetime import datetime

from bson import ObjectId
from fastapi import HTTPException
from pymongo.errors import DuplicateKeyError

from app.business.services.auth_service import get_client_id_from_user
from app.business.services.notificaciones_service import (
    notificar_por_email,
    notificar_por_sms,
)
from app.database.transactions import run_in_transaction
from app.persistence import (
    cliente_repository,
    inscripcion_repository,
    producto_repository,
    sequence_repository,
    transaccion_repository,
)

logger = logging.getLogger(__name__)


async def ejecutar_apertura_fondo(
    id_cliente: int,
    id_producto: int,
    avisar_operacion_sms_email: bool = False,
) -> dict:
    if inscripcion_repository.find_one(id_cliente, id_producto):
        raise HTTPException(
            status_code=409,
            detail="El cliente ya está suscrito a este fondo",
        )

    cliente, producto = _obtener_cliente_y_producto(id_cliente, id_producto)
    monto = _validar_saldo_apertura(cliente, producto)
    nombre = producto["nombre"]
    transaccion_id = sequence_repository.get_next_sequence_id_db("transacciones")
    cliente_actualizado = wrap_operation_in_mongo_session_open_cancel(
        lambda session: _registrar_apertura(
            session, id_cliente, id_producto, nombre, monto, transaccion_id
        ),
        "No se pudo completar la apertura del fondo",
    )
    mensaje = (
        f"Te has suscrito al fondo {nombre} "
        f"con un monto de {monto}. "
        f"ID transacción: {transaccion_id}"
    )
    return await _respuesta_fondo(
        avisar_operacion_sms_email,
        cliente_actualizado,
        transaccion_id,
        mensaje,
        "Suscripción Exitosa",
    )


async def ejecutar_cancelacion_fondo(
    id_cliente: int,
    id_producto: int,
    avisar_operacion_sms_email: bool = False,
) -> dict:
    inscripcion = inscripcion_repository.find_one(id_cliente, id_producto)
    if not inscripcion:
        raise HTTPException(
            status_code=404,
            detail="El cliente no está suscrito a este fondo",
        )

    _, producto = _obtener_cliente_y_producto(id_cliente, id_producto)
    monto = producto["monto_minimo"]
    nombre = producto["nombre"]
    transaccion_id = sequence_repository.get_next_sequence_id_db("transacciones")
    cliente_actualizado = wrap_operation_in_mongo_session_open_cancel(
        lambda session: _registrar_cancelacion(
            session,
            id_cliente,
            id_producto,
            monto,
            inscripcion,
            transaccion_id,
        ),
        "No se pudo completar la cancelación del fondo",
    )
    mensaje = (
        f"Has cancelado tu suscripción al fondo {nombre}. "
        f"ID transacción: {transaccion_id}"
    )
    return await _respuesta_fondo(
        avisar_operacion_sms_email,
        cliente_actualizado,
        transaccion_id,
        mensaje,
        "Cancelación de Suscripción",
    )


def obtener_historial_transaccion(user: dict, tipo: str | None = None) -> list[dict]:
    query: dict = {}
    if tipo:
        query["tipo"] = tipo
    if user.get("rol") != "admin":
        cliente_id = get_client_id_from_user(user)
        if cliente_id is None:
            raise HTTPException(
                status_code=403,
                detail="No se pudo identificar al cliente en el token",
            )
        query["idCliente"] = cliente_id

    transacciones = transaccion_repository.find(query)
    return [serialize_transaccion(t) for t in transacciones]


async def _respuesta_fondo(
    avisar_operacion_sms_email: bool,
    cliente: dict,
    transaccion_id: int,
    mensaje: str,
    asunto: str,
) -> dict:
    """La respuesta sale después del aviso. El mensaje HTTP es el mismo del canal."""
    respuesta = {
        "transaccion_id": transaccion_id,
        "mensaje": mensaje,
        "nuevo_saldo": cliente["saldo"],
    }
    if avisar_operacion_sms_email:
        respuesta["notificacion"] = await _post_event_notification(
            cliente, asunto, mensaje
        )
    return respuesta


def _obtener_cliente_y_producto(id_cliente: int, id_producto: int) -> tuple[dict, dict]:
    cliente = cliente_repository.find_by_id(id_cliente)
    producto = producto_repository.find_by_id(id_producto)
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return cliente, producto


def _validar_saldo_apertura(cliente: dict, producto: dict) -> int:
    if "saldo" not in cliente:
        raise HTTPException(
            status_code=400,
            detail="El cliente no tiene un saldo definido.",
        )
    monto = producto["monto_minimo"]
    if cliente["saldo"] < monto:
        raise HTTPException(
            status_code=400,
            detail=(
                "No tiene saldo disponible para vincularse "
                f"al fondo {producto['nombre']}"
            ),
        )
    return monto


def wrap_operation_in_mongo_session_open_cancel(operacion, detalle_si_falla: str):
    try:
        return run_in_transaction(operacion)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=detalle_si_falla) from exc


def _registrar_apertura(
    session,
    id_cliente: int,
    id_producto: int,
    nombre_fondo: str,
    monto: int,
    transaccion_id: int,
):
    cliente_actualizado = cliente_repository.descontar_saldo(
        id_cliente, monto, session=session
    )
    if not cliente_actualizado:
        raise HTTPException(
            status_code=400,
            detail=(
                "No tiene saldo disponible para vincularse "
                f"al fondo {nombre_fondo}"
            ),
        )

    fecha = datetime.now()
    _guardar_inscripcion(session, id_cliente, id_producto, monto, fecha)
    _guardar_transaccion_apertura(
        session, id_cliente, id_producto, monto, transaccion_id, fecha
    )
    return cliente_actualizado


def _guardar_inscripcion(session, id_cliente: int, id_producto: int, monto: int, fecha):
    try:
        inscripcion_repository.insert(
            {
                "idCliente": id_cliente,
                "idProducto": id_producto,
                "fecha": fecha,
                "tipo": "apertura",
                "monto": monto,
            },
            session=session,
        )
    except Exception as exc:
        _rollback_if_no_mongo_session(
            session,
            lambda: _deshacer_apertura(
                id_cliente, id_producto, monto, borrar_inscripcion=False
            ),
        )
        if isinstance(exc, DuplicateKeyError):
            raise HTTPException(
                status_code=409,
                detail="El cliente ya está suscrito a este fondo",
            ) from None
        raise HTTPException(
            status_code=500,
            detail="No se pudo registrar la inscripción",
        ) from None


def _guardar_transaccion_apertura(
    session,
    id_cliente: int,
    id_producto: int,
    monto: int,
    transaccion_id: int,
    fecha,
):
    try:
        transaccion_repository.insert(
            _datos_transaccion(
                transaccion_id, id_cliente, id_producto, monto, "apertura", fecha
            ),
            session=session,
        )
    except Exception:
        _rollback_if_no_mongo_session(
            session,
            lambda: _deshacer_apertura(
                id_cliente, id_producto, monto, borrar_inscripcion=True
            ),
        )
        raise HTTPException(
            status_code=500,
            detail="No se pudo registrar la transacción",
        ) from None


def _registrar_cancelacion(
    session,
    id_cliente: int,
    id_producto: int,
    monto: int,
    inscripcion: dict,
    transaccion_id: int,
):
    delete_result = inscripcion_repository.delete(
        id_cliente, id_producto, session=session
    )
    if delete_result.deleted_count == 0:
        raise HTTPException(
            status_code=404,
            detail="El cliente no está suscrito a este fondo",
        )

    cliente_actualizado = cliente_repository.depositar_saldo(
        id_cliente, monto, session=session
    )
    if not cliente_actualizado:
        _rollback_if_no_mongo_session(
            session,
            lambda: _restaurar_inscripcion(
                inscripcion, id_cliente, id_producto, monto
            ),
        )
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    _guardar_transaccion_cancelacion(
        session, id_cliente, id_producto, monto, inscripcion, transaccion_id
    )
    return cliente_actualizado


def _guardar_transaccion_cancelacion(
    session,
    id_cliente: int,
    id_producto: int,
    monto: int,
    inscripcion: dict,
    transaccion_id: int,
):
    try:
        transaccion_repository.insert(
            _datos_transaccion(
                transaccion_id,
                id_cliente,
                id_producto,
                monto,
                "cancelacion",
                datetime.now(),
            ),
            session=session,
        )
    except Exception:
        _rollback_if_no_mongo_session(
            session,
            lambda: _revertir_cancelacion(
                inscripcion, id_cliente, id_producto, monto
            ),
        )
        raise HTTPException(
            status_code=500,
            detail="No se pudo registrar la transacción de cancelación",
        ) from None


def _datos_transaccion(
    transaccion_id: int,
    id_cliente: int,
    id_producto: int,
    monto: int,
    tipo: str,
    fecha,
) -> dict:
    return {
        "transaccion_id": transaccion_id,
        "idCliente": id_cliente,
        "idProducto": id_producto,
        "fecha": fecha,
        "tipo": tipo,
        "monto": monto,
    }


def _revertir_cancelacion(
    inscripcion: dict,
    id_cliente: int,
    id_producto: int,
    monto: int,
) -> None:
    cliente_repository.descontar_saldo(id_cliente, monto)
    _restaurar_inscripcion(inscripcion, id_cliente, id_producto, monto)


def _rollback_if_no_mongo_session(session, accion) -> None:
    """Sin sesión de Mongo no hay rollback automático.
    Deshace a mano lo ya escrito antes del fallo: el saldo cobrado o
    reintegrado y, si alcanzó a guardarse, la inscripción. Con sesión,
    Mongo revierte esos cambios.
    """
    if session is None:
        accion()


def _deshacer_apertura(
    id_cliente: int,
    id_producto: int,
    monto: int,
    *,
    borrar_inscripcion: bool,
) -> None:
    try:
        if borrar_inscripcion:
            inscripcion_repository.delete(id_cliente, id_producto)
        devuelto = cliente_repository.depositar_saldo(id_cliente, monto)
    except Exception:
        devuelto = None
    if not devuelto:
        raise HTTPException(
            status_code=500,
            detail=(
                "No fue posible reversar el débito del saldo. "
                "La suscripción no quedó registrada y la operación "
                "requiere conciliación."
            ),
        )


def _restaurar_inscripcion(
    inscripcion: dict,
    id_cliente: int,
    id_producto: int,
    monto: int,
) -> None:
    try:
        inscripcion_repository.insert(
            {
                "idCliente": id_cliente,
                "idProducto": id_producto,
                "fecha": inscripcion.get("fecha", datetime.now()),
                "tipo": inscripcion.get("tipo", "apertura"),
                "monto": inscripcion.get("monto", monto),
            }
        )
    except Exception:
        raise HTTPException(
            status_code=500,
            detail=(
                "No fue posible restablecer la inscripción. "
                "El reintegro del saldo no quedó aplicado y la operación "
                "requiere conciliación."
            ),
        ) from None


async def _post_event_notification(cliente: dict, asunto: str, mensaje: str) -> str:
    """Envía el aviso y solo entonces informa qué pasó en cada canal."""
    email = str(cliente.get("email") or "").strip()
    telefono = str(cliente.get("telefono") or "").strip()
    resultados = await _launch_notification_observers(
        {
            "email": email,
            "telefono": telefono,
            "asunto": asunto,
            "mensaje": mensaje,
        }
    )
    return (
        f"{_texto_canal('email', email, resultados[0])}. "
        f"{_texto_canal('sms', telefono, resultados[1])}"
    )


def _texto_canal(canal: str, contacto: str, resultado) -> str:
    if not contacto:
        return f"No se encontró contacto para notificación por {canal}"
    if isinstance(resultado, Exception):
        return f"No se pudo enviar la notificación por {canal}"
    if resultado == "simulado":
        return f"Notificación de SMS simulada a {contacto}"
    destino = "email" if canal == "email" else "SMS"
    return f"Notificación enviada por {destino} a {contacto}"


async def _launch_notification_observers(evento: dict) -> list:
    """Email y SMS en paralelo. Si un canal falla, el otro igual termina."""
    resultados = list(
        await asyncio.gather(
            notificar_por_email(evento),
            notificar_por_sms(evento),
            return_exceptions=True,
        )
    )
    for resultado in resultados:
        if isinstance(resultado, Exception):
            logger.error("No se pudo enviar una notificación", exc_info=resultado)
    return resultados


def serialize_transaccion(transaccion: dict) -> dict:
    data = dict(transaccion)
    if "_id" in data:
        data["_id"] = str(data["_id"])
    if isinstance(data.get("idCliente"), ObjectId):
        data["idCliente"] = str(data["idCliente"])
    if isinstance(data.get("idProducto"), ObjectId):
        data["idProducto"] = str(data["idProducto"])
    return data
