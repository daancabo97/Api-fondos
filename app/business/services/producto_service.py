"""Capa de negocio — catálogo de fondos."""
from fastapi import HTTPException

from app.persistence import producto_repository

FONDOS_OFICIALES = [
    {"id": 1, "nombre": "FPV_BTG_PACTUAL_RECAUDADORA", "monto_minimo": 75000, "categoria": "FPV"},
    {"id": 2, "nombre": "FPV_BTG_PACTUAL_ECOPETROL", "monto_minimo": 125000, "categoria": "FPV"},
    {"id": 3, "nombre": "DEUDAPRIVADA", "monto_minimo": 50000, "categoria": "FIC"},
    {"id": 4, "nombre": "FDO-ACCIONES", "monto_minimo": 250000, "categoria": "FIC"},
    {"id": 5, "nombre": "FPV_BTG_PACTUAL_DINAMICA", "monto_minimo": 100000, "categoria": "FPV"},
]
def serialize_producto(producto: dict) -> dict:
    data = dict(producto)
    if "_id" in data:
        data["_id"] = str(data["_id"])
    return data


def listar_productos() -> list[dict]:
    return [serialize_producto(p) for p in producto_repository.find_all()]


def obtener_producto(producto_id: str) -> dict:
    producto = producto_repository.find_by_path_id(producto_id)
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return serialize_producto(producto)


def crear_producto(producto_data: dict) -> dict:
    producto_id = producto_repository.insert(producto_data).inserted_id
    return {"id": str(producto_id)}


def eliminar_producto(producto_id: str) -> dict:
    producto = producto_repository.find_by_path_id(producto_id)
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    result = producto_repository.delete_by_object_id(str(producto["_id"]))
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return {"message": "Producto eliminado correctamente"}
