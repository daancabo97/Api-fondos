from fastapi import APIRouter, HTTPException
from app.database import sucursales_collection
from app.schemas.sucursal import Sucursal
from bson import ObjectId

router = APIRouter()


@router.get("/sucursales/")
async def obtener_sucursales():
    sucursales = list(sucursales_collection.find())
    return sucursales


@router.post("/sucursales/")
async def crear_sucursal(sucursal: Sucursal):
    sucursal_id = sucursales_collection.insert_one(sucursal.dict()).inserted_id
    return {"id": str(sucursal_id)}


@router.get("/sucursales/{id}")
async def obtener_sucursal(id: str):
    sucursal = sucursales_collection.find_one({"_id": ObjectId(id)})
    if not sucursal:
        raise HTTPException(status_code=404, detail="Sucursal no encontrada")
    return sucursal

@router.delete("/sucursales/{id}")
async def eliminar_sucursal(id: str):
    result = sucursales_collection.delete_one({"_id": ObjectId(id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Sucursal no encontrada")
    return {"message": "Sucursal eliminada correctamente"}