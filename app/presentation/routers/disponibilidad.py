"""Capa de presentación - endpoints de disponibilidad."""
from fastapi import APIRouter, Depends

from app.business import disponibilidad_service
from app.presentation.dependencies.auth_deps import require_admin
from app.presentation.schemas.disponibilidad_DTO import Disponibilidad

router = APIRouter()


@router.get("/disponibilidad/")
async def listar_disponibilidad():
    return disponibilidad_service.listar_disponibilidad()


@router.get("/disponibilidad/{id}")
async def obtener_disponibilidad_por_id(id: str):
    return disponibilidad_service.obtener_disponibilidad(id)


@router.post("/disponibilidad/")
async def crear_disponibilidad(
    disponibilidad: Disponibilidad,
    _user=Depends(require_admin),
):
    return disponibilidad_service.crear_disponibilidad(disponibilidad.model_dump())


@router.put("/disponibilidad/{id}")
async def actualizar_disponibilidad(
    id: str,
    disponibilidad: Disponibilidad,
    _user=Depends(require_admin),
):
    return disponibilidad_service.actualizar_disponibilidad(
        id, disponibilidad.model_dump()
    )


@router.delete("/disponibilidad/{id}")
async def eliminar_disponibilidad(id: str, _user=Depends(require_admin)):
    return disponibilidad_service.eliminar_disponibilidad(id)
