from fastapi import APIRouter, HTTPException
from app.database import visitan_collection
from app.database import clientes_collection, sucursales_collection
from app.schemas.visita_DTO import Visita
from bson import ObjectId

router = APIRouter()

def visita_serializer(visita) -> dict:
    """Convierte los ObjectId y limpia el campo _id. Devuelve idSucursal e idCliente como int y agrega los nombres relacionados."""
    data = {}
    data["id"] = str(visita["_id"])
    for k, v in visita.items():
        if k != "_id":
            if k in ("idSucursal", "idCliente"):
                try:
                    data[k] = int(v)
                except (ValueError, TypeError):
                    data[k] = v
            else:
                data[k] = v
    # Buscar nombre del cliente
    cliente = clientes_collection.find_one({"id": data["idCliente"]})
    data["nombreCliente"] = cliente["nombre"] if cliente else None
    # Buscar apelldido del cliente
    data["apellidoCliente"] = cliente["apellidos"] if cliente else None
    # Buscar nombre de la sucursal
    sucursal = sucursales_collection.find_one({"id": data["idSucursal"]})
    data["nombreSucursal"] = sucursal["nombre"] if sucursal else None
    return data


@router.post("/visitas/")
async def registrar_visita(visita: Visita):
    # Permitir idSucursal e idCliente como string o entero
    visita_dict = visita.dict()
    # Convertir a string para mantener consistencia en la base de datos
    visita_dict["idSucursal"] = str(visita_dict["idSucursal"])
    visita_dict["idCliente"] = str(visita_dict["idCliente"])
    visita_id = visitan_collection.insert_one(visita_dict).inserted_id
    return {"id": str(visita_id)}


@router.get("/visitas/")
async def obtener_visitas():
    visitas = list(visitan_collection.find())
    visitas_serializadas = [visita_serializer(visita) for visita in visitas]
    return visitas_serializadas


@router.get("/visitas/sucursal/{idSucursal}")
async def obtener_visitas_por_sucursal(idSucursal: str):
    # Buscar por idSucursal como string y como entero (ambos)
    visitas = list(visitan_collection.find({"idSucursal": {"$in": [str(idSucursal), idSucursal]}}))
    if not visitas:
        raise HTTPException(status_code=404, detail="No se encontraron visitas para esta sucursal")
    visitas_serializadas = [visita_serializer(visita) for visita in visitas]
    return visitas_serializadas


@router.get("/visitas/cliente/{idCliente}")
async def obtener_visitas_por_cliente(idCliente: str):
    visitas = list(visitan_collection.find({"idCliente": {"$in": [str(idCliente), idCliente]}}))
    if not visitas:
        raise HTTPException(status_code=404, detail="No se encontraron visitas para este cliente")
    visitas_serializadas = [visita_serializer(visita) for visita in visitas]
    return visitas_serializadas
