"""Capa de negocio — autenticación, JWT, contraseñas y reglas RBAC."""
import re
from datetime import datetime, timedelta
from typing import Any

from fastapi import HTTPException, status
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.database.config import SECRET_KEY
from app.persistence import cliente_repository, revoked_token_repository


ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
SPECIAL_CHARS = "*#&_-."
_ALLOWED_PASSWORD_PATTERN = re.compile(r"^[A-Za-z0-9*#&_.\-]+$")
_SPECIAL_CHAR_PATTERN = re.compile(r"[*#&_.\-]")


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def password_requirements_message() -> str:
    return (
        "La contraseña debe tener al menos 8 caracteres, una mayúscula, "
        "una minúscula, un número y un carácter especial (*#&_.-). "
    )


def is_strong_password(password: str) -> bool:
    if len(password) < 8 or not _ALLOWED_PASSWORD_PATTERN.match(password):
        return False
    return (
        re.search(r"[A-Z]", password) is not None
        and re.search(r"[a-z]", password) is not None
        and re.search(r"[0-9]", password) is not None
        and _SPECIAL_CHAR_PATTERN.search(password) is not None
    )


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta=None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict[str, Any]:
    if revoked_token_repository.is_revoked(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token revocado",
        )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido",
            )
        return {
            "user_id": user_id,
            "rol": payload.get("rol", "cliente"),
            "cliente_id": payload.get("cliente_id"),
            "token": token,
        }
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
        )


def revoke_token(token: str) -> None:
    revoked_token_repository.revoke(token)


def get_client_id_from_user(user: dict[str, Any]) -> int | None:
    if user.get("cliente_id") is not None:
        return int(user["cliente_id"])
    cliente = cliente_repository.find_by_object_id(user["user_id"])
    if cliente and cliente.get("id") is not None:
        return int(cliente["id"])
    return None


def assert_own_client(user: dict[str, Any], id_cliente: int) -> None:
    if user.get("rol") == "admin":
        return
    token_client_id = get_client_id_from_user(user)
    if token_client_id is None or token_client_id != id_cliente:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No puede acceder a datos de otro cliente",
        )


def assert_access_to_client_path(user: dict[str, Any], id_param: str) -> int:
    """Devuelve el id numérico si ese usuario puede acceder al cliente de la ruta."""
    if user.get("rol") == "admin":
        return _id_de_cliente_existente(id_param)

    cliente = _cliente_del_token(user)
    if not _ruta_es_del_cliente(id_param, cliente, user["user_id"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No puede acceder a datos de otro cliente",
        )
    return int(cliente["id"])


def _id_de_cliente_existente(id_param: str) -> int:
    id_cliente = cliente_repository.resolve_id_from_path(id_param)
    if id_cliente is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente no encontrado",
        )
    return id_cliente


def _cliente_del_token(user: dict[str, Any]) -> dict:
    cliente = cliente_repository.find_by_object_id(user.get("user_id", ""))
    if not cliente or cliente.get("id") is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente no encontrado",
        )
    return cliente


def _ruta_es_del_cliente(id_param: str, cliente: dict, user_id: str) -> bool:
    if id_param.isdigit():
        return int(id_param) == int(cliente["id"])
    return id_param == user_id


def assert_admin(user: dict[str, Any]) -> dict[str, Any]:
    if user.get("rol") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requiere rol administrador",
        )
    return user
