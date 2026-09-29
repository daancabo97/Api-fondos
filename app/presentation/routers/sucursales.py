"""Capa de presentación - endpoints de sucursales."""
from fastapi import APIRouter, Depends

from app.business import sucursal_service
from app.presentation.dependencies.auth_deps import require_admin
from app.presentation.schemas.sucursal_DTO import Sucursal

router = APIRouter()


@router.get("/sucursales/")
async def obtener_sucursales():
    return sucursal_service.listar_sucursales()


@router.get("/sucursales/{id}")
async def obtener_sucursal(id: str):
    return sucursal_service.obtener_sucursal(id)


@router.post("/sucursales/")
async def crear_sucursal(sucursal: Sucursal, _user=Depends(require_admin)):
    return sucursal_service.crear_sucursal(sucursal.model_dump())


@router.delete("/sucursales/{id}")
async def eliminar_sucursal(id: str, _user=Depends(require_admin)):
    return sucursal_service.eliminar_sucursal(id)
