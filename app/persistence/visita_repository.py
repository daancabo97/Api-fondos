"""Capa de persistencia - acceso a la colección visitas."""
from app.database.connection import db

_collection = db["visitas"]
_LEGACY_COLLECTION = "visitan"


def _visita_key(doc: dict) -> tuple:
    """Clave de negocio para deduplicar visitas al fusionar colecciones."""
    fecha = doc.get("fechaVisita", doc.get("fecha"))
    return (doc.get("idSucursal"), doc.get("idCliente"), str(fecha) if fecha else None)


def ensure_collection() -> None:
    """
    Unifica la colección legacy visitan → visitas.

    - Solo visitan: renombra a visitas.
    - visitan + visitas: copia documentos faltantes a visitas y elimina visitan.
    - Solo visitas: no hace nada.
    """
    cols = set(db.list_collection_names())
    if _LEGACY_COLLECTION not in cols:
        return

    legacy = db[_LEGACY_COLLECTION]
    if "visitas" not in cols:
        legacy.rename("visitas")
        return

    existing_keys = {_visita_key(v) for v in _collection.find()}
    to_insert: list[dict] = []
    for doc in legacy.find():
        key = _visita_key(doc)
        if key in existing_keys:
            continue
        doc_copy = {k: v for k, v in doc.items() if k != "_id"}
        to_insert.append(doc_copy)
        existing_keys.add(key)

    if to_insert:
        _collection.insert_many(to_insert)
    legacy.drop()


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
