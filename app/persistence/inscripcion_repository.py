"""Capa de persistencia  acceso a la colección inscripciones."""
from app.database.connection import db

_collection = db["inscripciones"]


def ensure_indexes() -> None:
    """Índice único cliente+fondo. Si no se crea, el arranque debe fallar."""
    _collection.create_index(
        [("idCliente", 1), ("idProducto", 1)],
        unique=True,
        name="uniq_inscripcion_cliente_producto",
    )


def find_one(id_cliente: int, id_producto: int) -> dict | None:
    return _collection.find_one({"idCliente": id_cliente, "idProducto": id_producto})


def insert(inscripcion: dict, session=None):
    kwargs = {"session": session} if session is not None else {}
    return _collection.insert_one(inscripcion, **kwargs)


def delete(id_cliente: int, id_producto: int, session=None):
    kwargs = {"session": session} if session is not None else {}
    return _collection.delete_one(
        {"idCliente": id_cliente, "idProducto": id_producto}, **kwargs
    )
