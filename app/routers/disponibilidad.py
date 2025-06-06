from fastapi import APIRouter, HTTPException
from app.database import disponibilidad_collection
from app.schemas.disponibilidad_DTO import Disponibilidad
from bson import ObjectId

router = APIRouter()


@router.get("/disponibilidad/")
async def obtener_disponibilidad():
    disponibilidad = list(disponibilidad_collection.find())
    return disponibilidad


@router.post("/disponibilidad/")
async def crear_disponibilidad(disponibilidad: Disponibilidad):
    disponibilidad_id = disponibilidad_collection.insert_one(disponibilidad.dict()).inserted_id
    return {"id": str(disponibilidad_id)}


@router.get("/disponibilidad/{idSucursal}")
async def obtener_disponibilidad_por_sucursal(idSucursal: str):
    disponibilidad = list(disponibilidad_collection.find({"idSucursal": idSucursal}))
    if not disponibilidad:
        raise HTTPException(status_code=404, detail="No se encontró disponibilidad para esta sucursal")
    return disponibilidad
