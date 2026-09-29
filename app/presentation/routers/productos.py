"""Capa de presentación - endpoints de productos."""
from fastapi import APIRouter, Depends

from app.business import producto_service
from app.presentation.dependencies.auth_deps import require_admin
from app.presentation.schemas.producto_DTO import Producto

router = APIRouter()


@router.get("/productos/")
async def obtener_productos():
    return producto_service.listar_productos()


@router.get("/productos/{producto_id}")
async def obtener_producto(producto_id: str):
    return producto_service.obtener_producto(producto_id)


@router.post("/productos/")
async def crear_producto(producto: Producto, _user=Depends(require_admin)):
    return producto_service.crear_producto(producto.model_dump())


@router.delete("/productos/{producto_id}")
async def eliminar_producto(producto_id: str, _user=Depends(require_admin)):
    return producto_service.eliminar_producto(producto_id)
