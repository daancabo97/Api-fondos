"""Capa de persistencia - generador de IDs secuenciales (colección counters)."""
from pymongo import ReturnDocument

from app.database.connection import db


def sync_client_sequence() -> None:
    """Alinea el contador con el max(id) existente — evita ids duplicados."""
    ultimo = db.clientes.find_one(sort=[("id", -1)], projection={"id": 1})
    max_id = int(ultimo["id"]) if ultimo and ultimo.get("id") is not None else 0
    db.counters.update_one(
        {"_id": "clientes"},
        {"$max": {"seq": max_id}},
        upsert=True,
    )


def get_next_sequence(name: str) -> int:
    """Obtiene el siguiente ID de la secuencia."""
    counter = db.counters.find_one_and_update(
        {"_id": name},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=ReturnDocument.AFTER,
    )
    return counter["seq"]


def get_next_client_id() -> int:
    """Se encarga de generar un id de cliente único."""
    sync_client_sequence()
    for _ in range(100):
        candidate = get_next_sequence("clientes")
        if db.clientes.find_one({"id": candidate}, projection={"_id": 1}) is None:
            return candidate
    raise RuntimeError("No se pudo generar un id de cliente único")
