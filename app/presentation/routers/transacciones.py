"""Capa de presentación - endpoints de transacciones."""
from fastapi import APIRouter, BackgroundTasks, Depends

from app.business import auth_service, notificaciones_service, transaccion_service
from app.presentation.dependencies.auth_deps import require_authenticated
from app.presentation.schemas.transaccion_DTO import Transaccion

router = APIRouter()


async def _notificar_cliente(
    background_tasks: BackgroundTasks,
    cliente: dict,
    asunto: str,
    mensaje: str,
) -> str:
    canal, contacto = notificaciones_service.obtener_canal_contacto_notificacion(cliente)
    if not canal or not contacto:
        pref = cliente.get("canal_notificacion", "email")
        return f"No se encontró contacto para notificación por {pref}"
    background_tasks.add_task(
        notificaciones_service.enviar_notificacion, canal, contacto, asunto, mensaje
    )
    return f"Notificación programada por {canal} a {contacto}"


@router.post("/transacciones/apertura/")
async def suscribirse_fondo(
    transaccion: Transaccion,
    background_tasks: BackgroundTasks,
    user=Depends(require_authenticated),
):
    auth_service.assert_own_client(user, int(transaccion.idCliente))
    resultado = transaccion_service.ejecutar_apertura_fondo(
        int(transaccion.idCliente), int(transaccion.idProducto)
    )
    mensaje_notif = await _notificar_cliente(
        background_tasks,
        resultado["cliente"],
        "Suscripción Exitosa",
        f"Te has suscrito al fondo {resultado['nombre_fondo']} "
        f"con un monto de {resultado['monto']}. "
        f"ID transacción: {resultado['transaccion_id']}",
    )
    return {
        "transaccion_id": resultado["transaccion_id"],
        "mensaje": resultado["mensaje"],
        "nuevo_saldo": resultado["nuevo_saldo"],
        "notificacion": mensaje_notif,
    }


@router.post("/transacciones/cancelacion/")
async def cancelar_suscripcion_fondo(
    transaccion: Transaccion,
    background_tasks: BackgroundTasks,
    user=Depends(require_authenticated),
):
    auth_service.assert_own_client(user, int(transaccion.idCliente))
    resultado = transaccion_service.ejecutar_cancelacion_fondo(
        int(transaccion.idCliente), int(transaccion.idProducto)
    )
    mensaje_notif = await _notificar_cliente(
        background_tasks,
        resultado["cliente"],
        "Cancelación de Suscripción",
        f"Has cancelado tu suscripción al fondo {resultado['nombre_fondo']}. "
        f"ID transacción: {resultado['transaccion_id']}",
    )
    return {
        "transaccion_id": resultado["transaccion_id"],
        "mensaje": resultado["mensaje"],
        "nuevo_saldo": resultado["nuevo_saldo"],
        "notificacion": mensaje_notif,
    }


@router.get("/transacciones/")
async def ver_historial_transacciones(
    tipo: str = None,
    user=Depends(require_authenticated),
):
    return transaccion_service.obtener_historial(user, tipo)
