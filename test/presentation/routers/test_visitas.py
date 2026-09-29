import uuid

from test.business.services.auth_test_support import (
    admin_user,
    auth_headers_for_email,
    cliente_user,
)
from test.presentation.api_client import api_client

VISITA_SUCURSAL_ID = 88051


class TestVisitas:
    def test_registrar_y_listar_por_cliente(self):
        user = cliente_user()
        headers = user["headers"]
        admin = admin_user()
        client = api_client()

        client.post(
            "/sucursales/",
            json={"id": VISITA_SUCURSAL_ID, "nombre": "Sucursal Visita", "ciudad": "Bogotá"},
            headers=admin,
        )
        crear = client.post(
            "/visitas/",
            json={
                "idSucursal": VISITA_SUCURSAL_ID,
                "idCliente": user["id"],
                "fechaVisita": "2026-01-15",
            },
            headers=headers,
        )
        assert crear.status_code == 200
        assert "id" in crear.json()

        listado = client.get(f"/visitas/cliente/{user['id']}", headers=headers)
        assert listado.status_code == 200
        assert any(v["idSucursal"] == VISITA_SUCURSAL_ID for v in listado.json())

    def test_admin_listar_todas(self):
        response = api_client().get("/visitas/", headers=admin_user())
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_admin_listar_por_sucursal(self):
        user = cliente_user()
        admin = admin_user()
        client = api_client()
        client.post(
            "/sucursales/",
            json={"id": VISITA_SUCURSAL_ID, "nombre": "S Visita", "ciudad": "Bogotá"},
            headers=admin,
        )
        client.post(
            "/visitas/",
            json={
                "idSucursal": VISITA_SUCURSAL_ID,
                "idCliente": user["id"],
                "fechaVisita": "2026-02-01",
            },
            headers=user["headers"],
        )
        response = client.get(
            f"/visitas/sucursal/{VISITA_SUCURSAL_ID}",
            headers=admin,
        )
        assert response.status_code == 200

    def test_cliente_sin_visitas(self):
        email = f"novisita.{uuid.uuid4().hex[:8]}@gmail.com"
        client = api_client()
        client.post(
            "/clientes/",
            json={
                "cliente": {
                    "nombre": "Sin",
                    "apellidos": "Visita",
                    "ciudad": "Bogotá",
                    "saldo": 100000,
                    "email": email,
                    "telefono": "+573004444444",
                    "canal_notificacion": "email",
                },
                "password": "Password123*",
            },
        )
        from app.persistence import cliente_repository

        cid = cliente_repository.find_by_email(email)["id"]

        response = client.get(f"/visitas/cliente/{cid}", headers=auth_headers_for_email(email))
        assert response.status_code == 404
