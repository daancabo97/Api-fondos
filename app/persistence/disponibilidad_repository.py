"""Capa de persistencia - acceso a la colección disponibilidad."""
from bson import ObjectId

from app.database.connection import db

_collection = db["disponibilidad"]


def find_all() -> list[dict]:
    return list(_collection.find())


def find_by_sucursal_id(id_sucursal: int) -> list[dict]:
    return list(_collection.find({"idSucursal": id_sucursal}))


def find_by_object_id(id_param: str) -> dict | None:
    try:
        return _collection.find_one({"_id": ObjectId(id_param)})
    except Exception:
        return None


def insert(disponibilidad: dict):
    return _collection.insert_one(disponibilidad)


def update_by_object_id(id_param: str, data: dict, session=None):
    try:
        kwargs = {"session": session} if session is not None else {}
        return _collection.update_one(
            {"_id": ObjectId(id_param)}, {"$set": data}, **kwargs
        )
    except Exception:
        return None


def delete_by_object_id(id_param: str, session=None):
    kwargs = {"session": session} if session is not None else {}
    return _collection.delete_one({"_id": ObjectId(id_param)}, **kwargs)
