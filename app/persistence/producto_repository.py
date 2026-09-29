"""Capa de persistencia - acceso a la colección productos."""
from bson import ObjectId

from app.database.connection import db

_collection = db["productos"]


def find_all() -> list[dict]:
    return list(_collection.find())


def find_by_id(id_producto: int) -> dict | None:
    return _collection.find_one({"id": id_producto})


def find_by_path_id(id_param: str) -> dict | None:
    if id_param.isdigit():
        return find_by_id(int(id_param))
    try:
        return _collection.find_one({"_id": ObjectId(id_param)})
    except Exception:
        return None


def insert(producto: dict):
    return _collection.insert_one(producto)


def delete_by_object_id(producto_id: str):
    return _collection.delete_one({"_id": ObjectId(producto_id)})
