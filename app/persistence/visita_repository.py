"""Capa de persistencia - acceso a la colección visitas."""
from app.database.connection import db

_collection = db["visitas"]


def find_all() -> list[dict]:
    return list(_collection.find())


def find_by_sucursal(id_sucursal: int) -> list[dict]:
    return list(
        _collection.find({"idSucursal": {"$in": [id_sucursal, str(id_sucursal)]}})
    )


def find_by_cliente(id_cliente: int) -> list[dict]:
    return list(
        _collection.find({"idCliente": {"$in": [id_cliente, str(id_cliente)]}})
    )


def insert(visita: dict):
    return _collection.insert_one(visita)
