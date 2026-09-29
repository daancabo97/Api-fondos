"""Capa de persistencia - acceso a la colección transacciones."""
from app.database.connection import db

_collection = db["transacciones"]


def find(query: dict | None = None) -> list[dict]:
    return list(_collection.find(query or {}))


def insert(transaccion: dict, session=None):
    kwargs = {"session": session} if session is not None else {}
    return _collection.insert_one(transaccion, **kwargs)
