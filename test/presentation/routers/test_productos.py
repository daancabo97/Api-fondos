"""Tests — app.presentation.routers.productos"""
from test.business.services.auth_test_support import admin_user, cliente_user
from test.presentation.api_client import api_client


class TestListado:
    def test_obtener_productos_publico(self):
        response = api_client().get("/productos/")
        assert response.status_code == 200
        assert len(response.json()) >= 5

    def test_catalogo_fondos_oficial(self):
        response = api_client().get("/productos/")
        assert response.status_code == 200
        nombres = {p.get("nombre") for p in response.json()}
        assert "FPV_BTG_PACTUAL_RECAUDADORA" in nombres
        assert "DEUDAPRIVADA" in nombres


class TestObtener:
    def test_get_por_id_y_object_id(self):
        client = api_client()
        listado = client.get("/productos/")
        producto = listado.json()[0]

        assert client.get(f"/productos/{producto['id']}").status_code == 200
        assert client.get(f"/productos/{producto['_id']}").status_code == 200
        assert client.get("/productos/id-invalido").status_code == 404


class TestCrear:
    def test_crear_producto_requiere_admin(self):
        user = cliente_user()
        response = api_client().post(
            "/productos/",
            json={"id": 99, "nombre": "Test", "monto_minimo": 1000, "categoria": "FPV"},
            headers=user["headers"],
        )
        assert response.status_code == 403


class TestEliminar:
    def test_delete_por_id_numerico(self):
        client = api_client()
        headers = admin_user()
        temp_id = 99001
        crear = client.post(
            "/productos/",
            json={
                "id": temp_id,
                "nombre": "FONDO_TEST_DELETE",
                "monto_minimo": 1000,
                "categoria": "TEST",
            },
            headers=headers,
        )
        assert crear.status_code == 200

        borrar = client.delete(f"/productos/{temp_id}", headers=headers)
        assert borrar.status_code == 200
        assert client.get(f"/productos/{temp_id}").status_code == 404
        assert client.delete("/productos/id-invalido", headers=headers).status_code == 404
