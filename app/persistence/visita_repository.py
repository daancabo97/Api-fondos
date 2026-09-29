"""Capa de persistencia - acceso a la colección visitas."""
from app.database.connection import db

_collection = db["visitas"]
_LEGACY_COLLECTION = "visitan"


def _visita_key(doc: dict) -> tuple:
    fecha = doc.get("fechaVisita", doc.get("fecha"))
    return (doc.get("idSucursal"), doc.get("idCliente"), str(fecha) if fecha else None)


def ensure_collection() -> None:
    """Unifica la colección legacy visitan → visitas."""
    colecciones = set(db.list_collection_names())
    if _LEGACY_COLLECTION not in colecciones:
        return

    legacy = db[_LEGACY_COLLECTION]
    if _collection.name not in colecciones:
        legacy.rename(_collection.name)
        return

    _copiar_visitas_faltantes(legacy)
    legacy.drop()


def _documento_sin_id(doc: dict) -> dict:
    return {clave: valor for clave, valor in doc.items() if clave != "_id"}


def _copiar_visitas_faltantes(legacy) -> None:
    """Copia a visitas los documentos de visitan que aún no existen."""
    claves = {_visita_key(doc) for doc in _collection.find()}
    pendientes = []
    for doc in legacy.find():
        clave = _visita_key(doc)
        if clave in claves:
            continue
        claves.add(clave)
        pendientes.append(_documento_sin_id(doc))
    if pendientes:
        _collection.insert_many(pendientes)


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
