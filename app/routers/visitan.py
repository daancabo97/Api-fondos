from fastapi import APIRouter, HTTPException
from app.database import visitan_collection
from app.schemas.visita_DTO import Visita
from bson import ObjectId

router = APIRouter()


@router.post("/visitas/")
async def registrar_visita(visita: Visita):
    visita_id = visitan_collection.insert_one(visita.dict()).inserted_id
    return {"id": str(visita_id)}


@router.get("/visitas/")
async def obtener_visitas():
    visitas = list(visitan_collection.find())
    return visitas


@router.get("/visitas/sucursal/{idSucursal}")
async def obtener_visitas_por_sucursal(idSucursal: str):
    visitas = list(visitan_collection.find({"idSucursal": idSucursal}))
    if not visitas:
        raise HTTPException(status_code=404, detail="No se encontraron visitas para esta sucursal")
    return visitas


@router.get("/visitas/cliente/{idCliente}")
async def obtener_visitas_por_cliente(idCliente: str):
    visitas = list(visitan_collection.find({"idCliente": idCliente}))
    if not visitas:
        raise HTTPException(status_code=404, detail="No se encontraron visitas para este cliente")
    return visitas
