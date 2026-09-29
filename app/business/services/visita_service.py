"""Capa de negocio — registro de visitas cliente/sucursal."""
from fastapi import HTTPException

from app.persistence import cliente_repository, sucursal_repository, visita_repository


def serialize_visita(visita: dict) -> dict:
    data = {"id": str(visita["_id"])}
    for k, v in visita.items():
        if k != "_id":
            if k in ("idSucursal", "idCliente"):
                try:
                    data[k] = int(v)
                except (ValueError, TypeError):
                    data[k] = v
            else:
                data[k] = v
    cliente = cliente_repository.find_by_id(data.get("idCliente"))
    data["nombreCliente"] = cliente["nombre"] if cliente else None
    data["apellidoCliente"] = cliente["apellidos"] if cliente else None
    sucursal = sucursal_repository.find_by_id(data.get("idSucursal"))
    data["nombreSucursal"] = sucursal["nombre"] if sucursal else None
    return data


def registrar_visita(visita_data: dict) -> dict:
    visita_dict = dict(visita_data)
    visita_dict["idSucursal"] = int(visita_dict["idSucursal"])
    visita_dict["idCliente"] = int(visita_dict["idCliente"])
    visita_id = visita_repository.insert(visita_dict).inserted_id
    return {"id": str(visita_id)}


def listar_visitas() -> list[dict]:
    return [serialize_visita(v) for v in visita_repository.find_all()]


def listar_por_sucursal(id_sucursal: str) -> list[dict]:
    if not id_sucursal.isdigit():
        raise HTTPException(
            status_code=404,
            detail="No se encontraron visitas para esta sucursal",
        )
    visitas = visita_repository.find_by_sucursal(int(id_sucursal))
    if not visitas:
        raise HTTPException(
            status_code=404,
            detail="No se encontraron visitas para esta sucursal",
        )
    return [serialize_visita(v) for v in visitas]


def listar_por_cliente(id_cliente: str) -> list[dict]:
    if not id_cliente.isdigit():
        raise HTTPException(
            status_code=404,
            detail="No se encontraron visitas para este cliente",
        )
    visitas = visita_repository.find_by_cliente(int(id_cliente))
    if not visitas:
        raise HTTPException(
            status_code=404,
            detail="No se encontraron visitas para este cliente",
        )
    return [serialize_visita(v) for v in visitas]
