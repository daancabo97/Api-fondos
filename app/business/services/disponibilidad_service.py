"""Capa de negocio — disponibilidad producto/sucursal."""
from bson import ObjectId
from fastapi import HTTPException

from app.persistence import disponibilidad_repository, sucursal_repository


def _es_object_id(id_param: str) -> bool:
    if len(id_param) != 24:
        return False
    try:
        ObjectId(id_param)
        return True
    except Exception:
        return False


def serialize_disponibilidad(item: dict) -> dict:
    data = dict(item)
    data["id"] = str(data.pop("_id"))
    if "nombre" not in data:
        sucursal = sucursal_repository.find_by_id(int(data["idSucursal"]))
        data["nombre"] = sucursal["nombre"] if sucursal else None
    return data


def listar_disponibilidad() -> list[dict]:
    return [serialize_disponibilidad(item) for item in disponibilidad_repository.find_all()]


def obtener_disponibilidad(id_param: str) -> dict | list[dict]:
    """ObjectId → documento; entero → listado por sucursal."""
    if _es_object_id(id_param):
        item = disponibilidad_repository.find_by_object_id(id_param)
        if not item:
            raise HTTPException(status_code=404, detail="Disponibilidad no encontrada")
        return serialize_disponibilidad(item)
    return obtener_por_sucursal(id_param)


def obtener_por_sucursal(id_sucursal: str) -> list[dict]:
    if not id_sucursal.isdigit():
        raise HTTPException(
            status_code=404,
            detail="No se encontró disponibilidad para esta sucursal",
        )
    disponibilidad = disponibilidad_repository.find_by_sucursal_id(int(id_sucursal))
    if not disponibilidad:
        raise HTTPException(
            status_code=404,
            detail="No se encontró disponibilidad para esta sucursal",
        )
    return [serialize_disponibilidad(item) for item in disponibilidad]


def crear_disponibilidad(disponibilidad_data: dict) -> dict:
    disponibilidad_id = disponibilidad_repository.insert(disponibilidad_data).inserted_id
    return {"id": str(disponibilidad_id)}


def actualizar_disponibilidad(id_param: str, disponibilidad_data: dict) -> dict:
    if not _es_object_id(id_param):
        raise HTTPException(
            status_code=400,
            detail="El id debe ser un ObjectId de MongoDB (24 caracteres hex)",
        )
    if not disponibilidad_repository.find_by_object_id(id_param):
        raise HTTPException(status_code=404, detail="Disponibilidad no encontrada")
    resultado = disponibilidad_repository.update_by_object_id(
        id_param, disponibilidad_data
    )
    if not resultado or resultado.matched_count == 0:
        raise HTTPException(status_code=404, detail="Disponibilidad no encontrada")
    return {"message": "Disponibilidad actualizada correctamente"}


def eliminar_disponibilidad(id_param: str) -> dict:
    result = disponibilidad_repository.delete_by_object_id(id_param)
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Disponibilidad no encontrada")
    return {"message": "Disponibilidad eliminada correctamente"}
