"""Capa de negocio — apertura, cancelación e historial de transacciones."""
from datetime import datetime

from bson import ObjectId
from fastapi import HTTPException
from pymongo.errors import DuplicateKeyError

from app.business.services.auth_service import get_client_id_from_user
from app.database.transactions import run_in_transaction
from app.persistence import (
    cliente_repository,
    inscripcion_repository,
    producto_repository,
    sequence_repository,
    transaccion_repository,
)


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
            detail=f"No tiene saldo disponible para vincularse al fondo {producto['nombre']}",
        )
    return monto


def serialize_transaccion(transaccion: dict) -> dict:
    data = dict(transaccion)
    if "_id" in data:
        data["_id"] = str(data["_id"])
    if isinstance(data.get("idCliente"), ObjectId):
        data["idCliente"] = str(data["idCliente"])
    if isinstance(data.get("idProducto"), ObjectId):
        data["idProducto"] = str(data["idProducto"])
    return data


def _respuesta_apertura(
    transaccion_id: int,
    producto: dict,
    monto: int,
    cliente_actualizado: dict,
) -> dict:
    return {
        "transaccion_id": transaccion_id,
        "mensaje": f"Suscripción al fondo {producto['nombre']} realizada con éxito",
        "nuevo_saldo": cliente_actualizado["saldo"],
        "nombre_fondo": producto["nombre"],
        "monto": monto,
        "cliente": cliente_actualizado,
    }


def _respuesta_cancelacion(
    transaccion_id: int,
    producto: dict,
    cliente_actualizado: dict,
) -> dict:
    return {
        "transaccion_id": transaccion_id,
        "mensaje": f"Cancelación del fondo {producto['nombre']} realizada con éxito",
        "nuevo_saldo": cliente_actualizado["saldo"],
        "nombre_fondo": producto["nombre"],
        "cliente": cliente_actualizado,
    }


def _call_group_query_sesion_mongo(fn, *args, session=None):
    """Pasa la session a la consulta cuando existe, para agrupar el débito,
    la inscripción y el registro del tipo de la transacción.
    Si no hay session, llama la consulta sin ella.
    """
    if session is None:
        return fn(*args)
    return fn(*args, session)


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
                "La suscripción no quedó registrada y la operación requiere conciliación."
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
                "El reintegro del saldo no quedó aplicado y la operación requiere conciliación."
            ),
        ) from None


def ejecutar_apertura_fondo(id_cliente: int, id_producto: int) -> dict:
    if inscripcion_repository.find_one(id_cliente, id_producto):
        raise HTTPException(
            status_code=409,
            detail="El cliente ya está suscrito a este fondo",
        )

    cliente, producto = _obtener_cliente_y_producto(id_cliente, id_producto)
    monto = _validar_saldo_apertura(cliente, producto)
    transaccion_id = sequence_repository.get_next_sequence("transacciones")
    ahora = datetime.now()
    inscripcion_data = {
        "idCliente": id_cliente,
        "idProducto": id_producto,
        "fecha": ahora,
        "tipo": "apertura",
        "monto": monto,
    }
    transaccion_data = {
        "transaccion_id": transaccion_id,
        "idCliente": id_cliente,
        "idProducto": id_producto,
        "fecha": ahora,
        "tipo": "apertura",
        "monto": monto,
    }

    def aplicar(session):
        cliente_actualizado = _call_group_query_sesion_mongo(
            cliente_repository.descontar_saldo, id_cliente, monto, session=session
        )
        if not cliente_actualizado:
            raise HTTPException(
                status_code=400,
                detail=f"No tiene saldo disponible para vincularse al fondo {producto['nombre']}",
            )
        try:
            _call_group_query_sesion_mongo(inscripcion_repository.insert, inscripcion_data, session=session)
        except DuplicateKeyError:
            if session is None:
                _deshacer_apertura(id_cliente, id_producto, monto, borrar_inscripcion=False)
            raise HTTPException(
                status_code=409,
                detail="El cliente ya está suscrito a este fondo",
            ) from None
        except Exception:
            if session is None:
                _deshacer_apertura(id_cliente, id_producto, monto, borrar_inscripcion=False)
            raise HTTPException(
                status_code=500,
                detail="No se pudo registrar la inscripción",
            ) from None
        try:
            _call_group_query_sesion_mongo(transaccion_repository.insert, transaccion_data, session=session)
        except Exception:
            if session is None:
                _deshacer_apertura(id_cliente, id_producto, monto, borrar_inscripcion=True)
            raise HTTPException(
                status_code=500,
                detail="No se pudo registrar la transacción",
            ) from None
        return cliente_actualizado

    try:
        cliente_actualizado = run_in_transaction(aplicar)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="No se pudo completar la apertura del fondo",
        ) from exc

    return _respuesta_apertura(transaccion_id, producto, monto, cliente_actualizado)


def ejecutar_cancelacion_fondo(id_cliente: int, id_producto: int) -> dict:
    inscripcion = inscripcion_repository.find_one(id_cliente, id_producto)
    if not inscripcion:
        raise HTTPException(
            status_code=404,
            detail="El cliente no está suscrito a este fondo",
        )

    _cliente, producto = _obtener_cliente_y_producto(id_cliente, id_producto)
    monto = producto["monto_minimo"]
    transaccion_id = sequence_repository.get_next_sequence("transacciones")
    transaccion_data = {
        "transaccion_id": transaccion_id,
        "idCliente": id_cliente,
        "idProducto": id_producto,
        "fecha": datetime.now(),
        "tipo": "cancelacion",
        "monto": monto,
    }

    def aplicar(session):
        delete_result = _call_group_query_sesion_mongo(
            inscripcion_repository.delete, id_cliente, id_producto, session=session
        )
        if delete_result.deleted_count == 0:
            raise HTTPException(
                status_code=404,
                detail="El cliente no está suscrito a este fondo",
            )
        cliente_actualizado = _call_group_query_sesion_mongo(
            cliente_repository.depositar_saldo, id_cliente, monto, session=session
        )
        if not cliente_actualizado:
            if session is None:
                _restaurar_inscripcion(inscripcion, id_cliente, id_producto, monto)
            raise HTTPException(status_code=404, detail="Cliente no encontrado")
        try:
            _call_group_query_sesion_mongo(transaccion_repository.insert, transaccion_data, session=session)
        except Exception:
            if session is None:
                cliente_repository.descontar_saldo(id_cliente, monto)
                _restaurar_inscripcion(inscripcion, id_cliente, id_producto, monto)
            raise HTTPException(
                status_code=500,
                detail="No se pudo registrar la transacción de cancelación",
            ) from None
        return cliente_actualizado

    try:
        cliente_actualizado = run_in_transaction(aplicar)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="No se pudo completar la cancelación del fondo",
        ) from exc

    return _respuesta_cancelacion(transaccion_id, producto, cliente_actualizado)


def obtener_historial(user: dict, tipo: str | None = None) -> list[dict]:
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
