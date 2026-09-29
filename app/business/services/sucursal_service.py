"""Capa de negocio — gestión de sucursales."""
from fastapi import HTTPException

from app.persistence import sucursal_repository


def serialize_sucursal(sucursal: dict) -> dict:
    data = dict(sucursal)
    if "_id" in data:
        data["_id"] = str(data["_id"])
    return data


def listar_sucursales() -> list[dict]:
    return [serialize_sucursal(s) for s in sucursal_repository.find_all()]


def obtener_sucursal(id_param: str) -> dict:
    sucursal = sucursal_repository.find_by_path_id(id_param)
    if not sucursal:
        raise HTTPException(status_code=404, detail="Sucursal no encontrada")
    return serialize_sucursal(sucursal)


def crear_sucursal(sucursal_data: dict) -> dict:
    sucursal_id = sucursal_repository.insert(sucursal_data).inserted_id
    return {"id": str(sucursal_id)}


def eliminar_sucursal(id_param: str) -> dict:
    sucursal = sucursal_repository.find_by_path_id(id_param)
    if not sucursal:
        raise HTTPException(status_code=404, detail="Sucursal no encontrada")
    result = sucursal_repository.delete_by_object_id(str(sucursal["_id"]))
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Sucursal no encontrada")
    return {"message": "Sucursal eliminada correctamente"}
