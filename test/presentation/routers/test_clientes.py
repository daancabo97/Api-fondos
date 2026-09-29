import uuid

from test.business.services.auth_test_support import (
    admin_user,
    auth_headers_for_email,
    cliente_user,
)
from test.presentation.api_client import api_client


class TestRegistro:
    def _cliente_payload(self, email: str, **extra):
        return {
            "cliente": {
                "nombre": "Maria",
                "apellidos": "Lopez",
                "ciudad": "Medellin",
                "saldo": 500000,
                "email": email,
                "telefono": "+573001234567",
                "canal_notificacion": "email",
                **extra,
            },
            "password": "Password123*",
        }

    def test_crear_cliente(self):
        email = f"maria.lopez.{uuid.uuid4().hex[:8]}@gmail.com"
        response = api_client().post(
            "/clientes/",
            json={
                "cliente": {
                    "nombre": "Maria",
                    "apellidos": "Lopez",
                    "ciudad": "Medellin",
                    "saldo": 500000,
                    "email": email,
                    "telefono": "+573001234567",
                    "canal_notificacion": "email",
                },
                "password": "Password123*",
            },
        )
        assert response.status_code == 200
        assert "id" in response.json()

    def test_password_debil_rechazada(self):
        email = f"weak.pwd.{uuid.uuid4().hex[:8]}@gmail.com"
        response = api_client().post(
            "/clientes/",
            json={
                "cliente": {
                    "nombre": "Weak",
                    "apellidos": "Pwd",
                    "ciudad": "Bogotá",
                    "saldo": 100000,
                    "email": email,
                    "telefono": "+573009999998",
                    "canal_notificacion": "email",
                },
                "password": "Password123",
            },
        )
        assert response.status_code == 400
        assert "carácter especial" in response.json()["detail"].lower()

    def test_email_duplicado(self):
        email = f"dup.{uuid.uuid4().hex[:8]}@gmail.com"
        client = api_client()
        payload = self._cliente_payload(email)
        assert client.post("/clientes/", json=payload).status_code == 200
        dup = client.post("/clientes/", json=payload)
        assert dup.status_code == 400
        assert "registrado" in dup.json()["detail"].lower()

    def test_email_dominio_invalido(self):
        response = api_client().post(
            "/clientes/",
            json=self._cliente_payload("usuario@empresa.com"),
        )
        assert response.status_code == 422

    def test_telefono_vacio_rechazado(self):
        payload = self._cliente_payload(f"tel.{uuid.uuid4().hex[:8]}@gmail.com")
        payload["cliente"]["telefono"] = "   "
        assert api_client().post("/clientes/", json=payload).status_code == 422


class TestObtenerCliente:
    def test_obtener_por_id(self):
        user = cliente_user()
        response = api_client().get(f"/clientes/{user['id']}", headers=user["headers"])
        assert response.status_code == 200
        assert response.json()["email"] == user["email"]

    def test_otro_cliente_forbidden(self):
        user = cliente_user()
        otro_email = f"otro.{uuid.uuid4().hex[:8]}@gmail.com"
        api_client().post(
            "/clientes/",
            json={
                "cliente": {
                    "nombre": "Otro",
                    "apellidos": "User",
                    "ciudad": "Bogotá",
                    "saldo": 100000,
                    "email": otro_email,
                    "telefono": "+573002222222",
                    "canal_notificacion": "email",
                },
                "password": "Password123*",
            },
        )
        from app.persistence import cliente_repository

        otro = cliente_repository.find_by_email(otro_email)
        response = api_client().get(f"/clientes/{otro['id']}", headers=user["headers"])
        assert response.status_code == 403

    def test_admin_obtiene_cualquier_cliente(self):
        user = cliente_user()
        response = api_client().get(f"/clientes/{user['id']}", headers=admin_user())
        assert response.status_code == 200

    def test_cliente_inexistente_admin(self):
        response = api_client().get("/clientes/99999999", headers=admin_user())
        assert response.status_code == 404

    def test_obtener_por_object_id(self):
        user = cliente_user()
        from app.persistence import cliente_repository

        cliente = cliente_repository.find_by_email(user["email"])
        oid = str(cliente["_id"])
        response = api_client().get(f"/clientes/{oid}", headers=user["headers"])
        assert response.status_code == 200


class TestEliminarCliente:
    def test_eliminar_propio(self):
        email = f"del.{uuid.uuid4().hex[:8]}@gmail.com"
        client = api_client()
        client.post(
            "/clientes/",
            json={
                "cliente": {
                    "nombre": "Del",
                    "apellidos": "Me",
                    "ciudad": "Bogotá",
                    "saldo": 100000,
                    "email": email,
                    "telefono": "+573003333333",
                    "canal_notificacion": "email",
                },
                "password": "Password123*",
            },
        )
        headers = auth_headers_for_email(email)
        from app.persistence import cliente_repository

        cid = cliente_repository.find_by_email(email)["id"]
        assert client.delete(f"/clientes/{cid}", headers=headers).status_code == 200

    def test_admin_elimina_por_id(self):
        email = f"adm.del.{uuid.uuid4().hex[:8]}@gmail.com"
        client = api_client()
        reg = client.post(
            "/clientes/",
            json={
                "cliente": {
                    "nombre": "Adm",
                    "apellidos": "Del",
                    "ciudad": "Bogotá",
                    "saldo": 100000,
                    "email": email,
                    "telefono": "+573005555555",
                    "canal_notificacion": "email",
                },
                "password": "Password123*",
            },
        )
        cid = reg.json()["id"]
        assert client.delete(f"/clientes/{cid}", headers=admin_user()).status_code == 200


class TestActualizarSaldo:
    def test_cliente_inexistente(self):
        response = api_client().put(
            "/clientes/99999999?nuevo_saldo=1000",
            headers=admin_user(),
        )
        assert response.status_code == 404


class TestToken:
    def test_token_invalido(self):
        response = api_client().get(
            "/transacciones/",
            headers={"Authorization": "Bearer token.invalido"},
        )
        assert response.status_code == 401


class TestListadoAdmin:
    def test_obtener_clientes_requiere_admin(self):
        user = cliente_user()
        response = api_client().get("/clientes/", headers=user["headers"])
        assert response.status_code == 403

    def test_obtener_clientes_admin(self):
        response = api_client().get("/clientes/", headers=admin_user())
        assert response.status_code == 200
        assert isinstance(response.json(), list)


class TestLogin:
    def test_login_rate_limit(self):
        client = api_client()
        for i in range(5):
            response = client.post(
                "/login",
                json={"email": f"rate.limit.{i}@test.com", "password": "wrong"},
            )
            assert response.status_code == 401

        sexto = client.post(
            "/login",
            json={"email": "rate.limit.blocked@test.com", "password": "wrong"},
        )
        assert sexto.status_code == 429


class TestLogout:
    def test_logout_revoca_token(self):
        email = f"logout.{uuid.uuid4().hex[:8]}@gmail.com"
        client = api_client()
        client.post(
            "/clientes/",
            json={
                "cliente": {
                    "nombre": "Logout",
                    "apellidos": "Test",
                    "ciudad": "Bogotá",
                    "saldo": 100000,
                    "email": email,
                    "telefono": "+573007777777",
                    "canal_notificacion": "email",
                },
                "password": "Password123*",
            },
        )
        headers = auth_headers_for_email(email)

        assert client.post("/logout", headers=headers).status_code == 200

        response = client.get("/transacciones/", headers=headers)
        assert response.status_code == 401
        assert "revocado" in response.json()["detail"].lower()
