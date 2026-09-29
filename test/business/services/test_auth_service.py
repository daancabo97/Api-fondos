import pytest
from fastapi import HTTPException
from jose import jwt

from app.business.services import auth_service
from app.database.config import SECRET_KEY
from test.business.services.auth_test_support import CLIENTE_EMAIL, PASSWORD


class TestPassword:
    def test_is_strong_password_valida(self):
        assert auth_service.is_strong_password("Password123*") is True

    def test_is_strong_password_caracter_invalido(self):
        assert auth_service.is_strong_password("Password123!") is False

    def test_password_requirements_message(self):
        assert "carácter especial" in auth_service.password_requirements_message().lower()


class TestDecodeToken:
    def test_token_invalido(self):
        with pytest.raises(HTTPException) as exc:
            auth_service.decode_token("token.invalido")
        assert exc.value.status_code == 401

    def test_token_sin_sub(self):
        token = jwt.encode({"rol": "cliente"}, SECRET_KEY, algorithm="HS256")
        with pytest.raises(HTTPException) as exc:
            auth_service.decode_token(token)
        assert "inválido" in exc.value.detail.lower()


class TestVerifyPassword:
    def test_verify_password_cliente_seed(self):
        from app.persistence import cliente_repository

        cliente = cliente_repository.find_by_email(CLIENTE_EMAIL)
        assert auth_service.verify_password(PASSWORD, cliente["password"]) is True
        assert auth_service.verify_password("wrong", cliente["password"]) is False


class TestLoginService:
    def test_login_exitoso(self):
        from app.business.services import cliente_service

        result = cliente_service.login(CLIENTE_EMAIL, PASSWORD)
        assert result["token_type"] == "bearer"
        assert result["access_token"]


class TestGetClienteIdFromUser:
    def test_resuelve_por_object_id_si_falta_cliente_id(self):
        from app.persistence import cliente_repository

        cliente = cliente_repository.find_by_email(CLIENTE_EMAIL)
        user = {
            "user_id": str(cliente["_id"]),
            "rol": "cliente",
            "cliente_id": None,
        }
        assert auth_service.get_client_id_from_user(user) == cliente["id"]
