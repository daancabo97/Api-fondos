"""Capa de negocio — reglas de clientes, registro y login."""
from typing import Any

from fastapi import HTTPException, status

from app.business.services import auth_service
from app.persistence import cliente_repository, sequence_repository


def serialize_cliente(cliente: dict) -> dict:
    """Respuesta API: incluye rol, canal y teléfono. Omite password."""
    return {
        "id": cliente.get("id"),
        "object_id": str(cliente["_id"]) if "_id" in cliente else None,
        "nombre": cliente.get("nombre"),
        "apellidos": cliente.get("apellidos"),
        "ciudad": cliente.get("ciudad"),
        "saldo": cliente.get("saldo"),
        "email": cliente.get("email"),
        "rol": cliente.get("rol", "cliente"),
        "canal_notificacion": cliente.get("canal_notificacion", "email"),
        "telefono": cliente.get("telefono", ""),
    }


def listar_clientes() -> list[dict]:
    return [serialize_cliente(c) for c in cliente_repository.find_all()]


def registrar_cliente(cliente_data: dict, password: str) -> dict:
    email = cliente_data["email"]
    if cliente_repository.find_by_email(email):
        raise HTTPException(status_code=400, detail="El email ya está registrado")
    if not auth_service.is_strong_password(password):
        raise HTTPException(
            status_code=400,
            detail=auth_service.password_requirements_message(),
        )

    cliente_dict = {k: v for k, v in cliente_data.items() if v is not None}
    cliente_dict.pop("rol", None)
    cliente_dict["rol"] = "cliente"
    cliente_dict["id"] = sequence_repository.get_next_client_id()
    cliente_dict["password"] = auth_service.get_password_hash(password)

    resultado = cliente_repository.insert(cliente_dict)
    cliente_dict["_id"] = resultado.inserted_id
    return serialize_cliente(cliente_dict)


def obtener_cliente(id_param: str, user: dict[str, Any] | None = None) -> dict:
    """ obtienel cliente por id o object id """
    cliente = cliente_repository.find_by_path_id(id_param)
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return serialize_cliente(cliente)


def eliminar_cliente(id_param: str, user: dict[str, Any]) -> dict:
    auth_service.assert_access_to_client_path(user, id_param)
    cliente = cliente_repository.find_by_path_id(id_param)
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    if cliente_repository.delete_by_object_id(cliente["_id"]) == 0:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return {"mensaje": "Cliente eliminado correctamente"}


def actualizar_saldo(id_param: str, nuevo_saldo: int) -> dict:
    resultado = cliente_repository.update_saldo(id_param, nuevo_saldo)
    if not resultado or resultado.modified_count == 0:
        raise HTTPException(
            status_code=404,
            detail="Cliente no encontrado o saldo no actualizado",
        )
    return {"mensaje": "Saldo actualizado correctamente"}


def login(email: str, password: str) -> dict:
    cliente = cliente_repository.find_by_email(email)
    if not cliente or not auth_service.verify_password(password, cliente["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
        )
    token = auth_service.create_access_token(
        {
            "sub": str(cliente["_id"]),
            "rol": cliente.get("rol", "cliente"),
            "cliente_id": cliente.get("id"),
        }
    )
    return {
        "access_token": token,
        "token_type": "bearer",
        "rol": cliente.get("rol", "cliente"),
    }


def logout(token: str) -> dict:
    auth_service.revoke_token(token)
    return {"message": "Token revocado correctamente"}
