"""Capa de persistencia - acceso a la colección sucursales."""
from bson import ObjectId

from app.database.connection import db

_collection = db["sucursales"]


def find_all() -> list[dict]:
    return list(_collection.find())


def find_by_object_id(id_param: str) -> dict | None:
    return _collection.find_one({"_id": ObjectId(id_param)})


def find_by_id(id_sucursal: int) -> dict | None:
    return _collection.find_one({"id": id_sucursal})


def find_by_path_id(id_param: str) -> dict | None:
    if id_param.isdigit():
        return find_by_id(int(id_param))
    try:
        return find_by_object_id(id_param)
    except Exception:
        return None


def insert(sucursal: dict):
    return _collection.insert_one(sucursal)


def delete_by_object_id(id_param: str):
    return _collection.delete_one({"_id": ObjectId(id_param)})
