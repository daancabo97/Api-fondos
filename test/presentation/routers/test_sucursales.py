from test.business.services.auth_test_support import admin_user
from test.presentation.api_client import api_client


class TestListado:
    def test_obtener_sucursales_publico(self):
        response = api_client().get("/sucursales/")
        assert response.status_code == 200


class TestObtener:
    def test_obtener_por_id(self):
        headers = admin_user()
        temp_id = 99003
        client = api_client()
        client.post(
            "/sucursales/",
            json={"id": temp_id, "nombre": "Suc Get Test", "ciudad": "Medellín"},
            headers=headers,
        )
        response = client.get(f"/sucursales/{temp_id}")
        assert response.status_code == 200
        assert response.json()["nombre"] == "Suc Get Test"


class TestEliminar:
    def test_delete_por_id_numerico(self):
        client = api_client()
        headers = admin_user()
        temp_id = 99002
        crear = client.post(
            "/sucursales/",
            json={"id": temp_id, "nombre": "Sucursal Delete Test", "ciudad": "Bogotá"},
            headers=headers,
        )
        assert crear.status_code == 200

        borrar = client.delete(f"/sucursales/{temp_id}", headers=headers)
        assert borrar.status_code == 200
        assert client.get(f"/sucursales/{temp_id}").status_code == 404
