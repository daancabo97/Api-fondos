"""
Capa de presentación - inyección de dependencias para autenticación.
"""
from typing import Any

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.business import auth_service

bearer_scheme = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict[str, Any]:
    return auth_service.decode_token(credentials.credentials)


def require_authenticated(
    user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    return user


def require_admin(user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
    return auth_service.assert_admin(user)
