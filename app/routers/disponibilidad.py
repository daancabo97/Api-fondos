from fastapi import APIRouter, HTTPException
from app.database import disponibilidad_collection
from app.schemas.disponibilidad_DTO import Disponibilidad
from bson import ObjectId

router = APIRouter()


@router.get("/disponibilidad/")
async def obtener_disponibilidad():
    disponibilidad = list(disponibilidad_collection.find())
    # Convertir ObjectId a str para evitar errores de serialización
    for item in disponibilidad:
        item["_id"] = str(item["_id"])
        # Buscar el nombre de la sucursal si no está presente
        if "nombre" not in item:
            from app.database import sucursales_collection
            sucursal = sucursales_collection.find_one({"id": int(item["idSucursal"])})
            item["nombre"] = sucursal["nombre"] if sucursal else None
    return disponibilidad


@router.post("/disponibilidad/")
async def crear_disponibilidad(disponibilidad: Disponibilidad):
    disponibilidad_id = disponibilidad_collection.insert_one(disponibilidad.dict()).inserted_id
    return {"id": str(disponibilidad_id)}


@router.delete("/disponibilidad/{idSucursal}")
async def eliminar_disponibilidad(id: str):
    result = disponibilidad_collection.delete_one({"_id": ObjectId(id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Disponibilidad no encontrada")
    return {"message": "Disponibilidad eliminada correctamente"}


@router.get("/disponibilidad/{idSucursal}")
async def obtener_disponibilidad_por_sucursal(idSucursal: str):
    # Buscar solo por el campo _id de la sucursal (ObjectId referencial)
    disponibilidad = list(disponibilidad_collection.find({"_id": ObjectId(idSucursal)}))
    if not disponibilidad:
        raise HTTPException(status_code=404, detail="No se encontró disponibilidad para esta sucursal")
    for item in disponibilidad:
        item["_id"] = str(item["_id"])
    return disponibilidad