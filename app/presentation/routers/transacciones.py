"""Capa de presentación - endpoints de transacciones."""
from fastapi import APIRouter, Depends

from app.business import auth_service, transaccion_service
from app.presentation.dependencies.auth_deps import require_authenticated
from app.presentation.schemas.transaccion_DTO import Transaccion

router = APIRouter()


@router.post("/transacciones/apertura/")
async def suscribirse_fondo(
    transaccion: Transaccion,
    user=Depends(require_authenticated),
):
    auth_service.assert_own_client(user, int(transaccion.idCliente))
    resultado = await transaccion_service.ejecutar_apertura_fondo(
        int(transaccion.idCliente),
        int(transaccion.idProducto),
        avisar_operacion_sms_email=True,
    )
    return {
        "transaccion_id": resultado["transaccion_id"],
        "mensaje": resultado["mensaje"],
        "nuevo_saldo": resultado["nuevo_saldo"],
        "notificacion": resultado["notificacion"],
    }


@router.post("/transacciones/cancelacion/")
async def cancelar_suscripcion_fondo(
    transaccion: Transaccion,
    user=Depends(require_authenticated),
):
    auth_service.assert_own_client(user, int(transaccion.idCliente))
    resultado = await transaccion_service.ejecutar_cancelacion_fondo(
        int(transaccion.idCliente),
        int(transaccion.idProducto),
        avisar_operacion_sms_email=True,
    )
    return {
        "transaccion_id": resultado["transaccion_id"],
        "mensaje": resultado["mensaje"],
        "nuevo_saldo": resultado["nuevo_saldo"],
        "notificacion": resultado["notificacion"],
    }


@router.get("/transacciones/")
async def ver_historial_transacciones(
    tipo: str = None,
    user=Depends(require_authenticated),
):
    return transaccion_service.obtener_historial_transaccion(user, tipo)
