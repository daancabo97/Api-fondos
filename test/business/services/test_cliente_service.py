import uuid

import pytest
from fastapi import HTTPException

from app.business.services import cliente_service
from app.persistence import cliente_repository
from test.business.services.auth_test_support import cliente_user
from test.presentation.api_client import api_client


class TestObtenerCliente:
    def test_cliente_no_encontrado_en_jwt(self):
        user = {
            "user_id": "507f1f77bcf86cd799439011",
            "rol": "cliente",
            "cliente_id": 1,
        }
        with pytest.raises(HTTPException) as exc:
            cliente_service.obtener_cliente("1", user)
        assert exc.value.status_code == 404

    def test_id_entero(self):
        user = cliente_user()
        cliente = cliente_repository.find_by_email(user["email"])
        user_dict = {
            "user_id": str(cliente["_id"]),
            "rol": "cliente",
            "cliente_id": cliente["id"],
        }
        with pytest.raises(HTTPException) as exc:
            cliente_service.obtener_cliente(str(cliente["id"] + 99999), user_dict)
        assert exc.value.status_code == 403

    def test_object_id(self):
        user = cliente_user()
        cliente = cliente_repository.find_by_email(user["email"])
        user_dict = {
            "user_id": str(cliente["_id"]),
            "rol": "cliente",
            "cliente_id": cliente["id"],
        }
        with pytest.raises(HTTPException) as exc:
            cliente_service.obtener_cliente("507f1f77bcf86cd799439011", user_dict)
        assert exc.value.status_code == 403

    def test_admin_cliente_inexistente(self):
        with pytest.raises(HTTPException) as exc:
            cliente_service.obtener_cliente("99999999", {"rol": "admin"})
        assert exc.value.status_code == 404


class TestEliminarCliente:
    def test_admin_elimina_por_object_id(self):
        email = f"oid.del.{uuid.uuid4().hex[:8]}@gmail.com"
        client = api_client()
        reg = client.post(
            "/clientes/",
            json={
                "cliente": {
                    "nombre": "Oid",
                    "apellidos": "Del",
                    "ciudad": "Bogotá",
                    "saldo": 100000,
                    "email": email,
                    "telefono": "+573004444444",
                    "canal_notificacion": "email",
                },
                "password": "Password123*",
            },
        )
        assert reg.status_code == 200
        doc = cliente_repository.find_by_email(email)
        oid = str(doc["_id"])
        from test.business.services.auth_test_support import admin_user

        assert client.delete(f"/clientes/{oid}", headers=admin_user()).status_code == 200

    def test_cliente_no_encontrado_al_eliminar(self):
        user_dict = {
            "user_id": "507f1f77bcf86cd799439011",
            "rol": "cliente",
            "cliente_id": 1,
        }
        with pytest.raises(HTTPException) as exc:
            cliente_service.eliminar_cliente("1", user_dict)
        assert exc.value.status_code == 404

    def test_eliminar_id(self):
        user = cliente_user()
        cliente = cliente_repository.find_by_email(user["email"])
        user_dict = {
            "user_id": str(cliente["_id"]),
            "rol": "cliente",
            "cliente_id": cliente["id"],
        }
        with pytest.raises(HTTPException) as exc:
            cliente_service.eliminar_cliente(str(cliente["id"] + 99999), user_dict)
        assert exc.value.status_code == 403

    def test_admin_sin_registros_eliminados(self, monkeypatch):
        monkeypatch.setattr(
            cliente_repository,
            "delete_by_id",
            lambda _id: 0,
        )
        with pytest.raises(HTTPException) as exc:
            cliente_service.eliminar_cliente("1", {"rol": "admin"})
        assert exc.value.status_code == 404

    def test_admin_object_id_inexistente(self):
        with pytest.raises(HTTPException) as exc:
            cliente_service.eliminar_cliente(
                "507f1f77bcf86cd799439011",
                {"rol": "admin"},
            )
        assert exc.value.status_code == 404
