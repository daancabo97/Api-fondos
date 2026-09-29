"""Capa de presentación - endpoints HTTP de visitas."""
from fastapi import APIRouter, Depends

from app.business import auth_service, visita_service
from app.presentation.dependencies.auth_deps import require_admin, require_authenticated
from app.presentation.schemas.visita_DTO import Visita

router = APIRouter()


@router.post("/visitas/")
async def registrar_visita(visita: Visita, user=Depends(require_authenticated)):
    auth_service.assert_own_client(user, int(visita.idCliente))
    return visita_service.registrar_visita(visita.model_dump())


@router.get("/visitas/")
async def obtener_visitas(_user=Depends(require_admin)):
    return visita_service.listar_visitas()


@router.get("/visitas/sucursal/{idSucursal}")
async def obtener_visitas_por_sucursal(idSucursal: str, _user=Depends(require_admin)):
    return visita_service.listar_por_sucursal(idSucursal)


@router.get("/visitas/cliente/{idCliente}")
async def obtener_visitas_por_cliente(idCliente: str, user=Depends(require_authenticated)):
    auth_service.assert_own_client(user, int(idCliente))
    return visita_service.listar_por_cliente(idCliente)
