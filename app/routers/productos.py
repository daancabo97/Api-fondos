from fastapi import APIRouter, HTTPException
from app.database import productos_collection
from app.schemas.producto import Producto
from bson import ObjectId

router = APIRouter()

def producto_serializer(producto):
    producto["_id"] = str(producto["_id"])
    del producto["_id"]
    return producto

@router.get("/productos/")
async def obtener_productos():
    productos = list(productos_collection.find())
    productos_serializados = [producto_serializer(producto) for producto in productos]
    return productos_serializados


@router.post("/productos/")
async def crear_producto(producto: Producto):
    producto_id = productos_collection.insert_one(producto.dict()).inserted_id
    return {"id": str(producto_id)}


@router.delete("/productos/{producto_id}")
async def eliminar_producto(producto_id: str):
    result = productos_collection.delete_one({"_id": producto_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return {"message": "Producto eliminado correctamente"}
