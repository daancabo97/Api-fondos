"""Capa de persistencia - acceso a la colección clientes."""
from bson import ObjectId
from pymongo import ReturnDocument
from pymongo.errors import OperationFailure

from app.database.connection import db

_collection = db["clientes"]


def ensure_indexes() -> None:
    """Índices únicos: email e id (evita colisiones en GET /clientes/{id})."""
    try:
        _collection.create_index("id", unique=True, name="uniq_cliente_id")
        _collection.create_index("email", unique=True, name="uniq_cliente_email")
    except OperationFailure:
        pass


def find_all() -> list[dict]:
    return list(_collection.find().sort("_id", 1))


def find_by_id(id_cliente: int) -> dict | None:
    return _collection.find_one({"id": id_cliente})


def find_by_path_id(id_param: str) -> dict | None:
    if id_param.isdigit():
        return find_by_id(int(id_param))
    try:
        return _collection.find_one({"_id": ObjectId(id_param)})
    except Exception:
        return None


def resolve_id_from_path(id_param: str) -> int | None:
    cliente = find_by_path_id(id_param)
    if cliente and cliente.get("id") is not None:
        return int(cliente["id"])
    return None


def find_by_email(email: str) -> dict | None:
    return _collection.find_one({"email": email})


def find_by_object_id(user_id: str) -> dict | None:
    try:
        return _collection.find_one({"_id": ObjectId(user_id)})
    except Exception:
        return None


def insert(cliente: dict):
    return _collection.insert_one(cliente)


def delete_by_object_id(object_id) -> int:
    result = _collection.delete_one({"_id": object_id})
    return result.deleted_count


def delete_by_id(id_cliente: int) -> int:
    result = _collection.delete_many({"id": id_cliente})
    return result.deleted_count


def update_saldo(id_param: str, nuevo_saldo: int):
    cliente = find_by_path_id(id_param)
    if not cliente:
        return None
    return _collection.update_one(
        {"_id": cliente["_id"]}, {"$set": {"saldo": nuevo_saldo}}
    )


def update_saldo_by_id(id_cliente: int, nuevo_saldo: int):
    cliente = find_by_id(id_cliente)
    if not cliente:
        return None
    return _collection.update_one(
        {"_id": cliente["_id"]}, {"$set": {"saldo": nuevo_saldo}}
    )


def descontar_saldo(id_cliente: int, monto: int, session=None) -> dict | None:
    """ Resta el monto de vinculación del saldo del cliente en la apertura si el saldo alcanza.
        Si una cancelación ya reintegró el dinero y luego falla el registro,
        vuelve a restarlo para deshacer ese reintegro.
    """
    kwargs = {"session": session} if session is not None else {}
    return _collection.find_one_and_update(
        {"id": id_cliente, "saldo": {"$gte": monto}},
        {"$inc": {"saldo": -monto}},
        return_document=ReturnDocument.AFTER,
        **kwargs,
    )


def depositar_saldo(id_cliente: int, monto: int, session=None) -> dict | None:
    """Suma el monto de vinculación al saldo del cliente.
        - Cancelación: devolución por salida del fondo.
        - Fallo de suscripción: devolución si el cobro se realizó antes de fallar la inscripción/registro.
    """
    kwargs = {"session": session} if session is not None else {}
    return _collection.find_one_and_update(
        {"id": id_cliente},
        {"$inc": {"saldo": monto}},
        return_document=ReturnDocument.AFTER,
        **kwargs,
    )


def upsert_by_email(email: str, data: dict):
    return _collection.update_one({"email": email}, {"$set": data}, upsert=True)
