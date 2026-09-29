from test.business.services.auth_test_support import admin_user
from test.presentation.api_client import api_client

SUCURSAL_ID = 88050


class TestDisponibilidadCrud:
    def test_crear_listar_y_eliminar(self):
        client = api_client()
        headers = admin_user()
        client.post(
            "/sucursales/",
            json={"id": SUCURSAL_ID, "nombre": "Sucursal Test", "ciudad": "Bogotá"},
            headers=headers,
        )
        crear = client.post(
            "/disponibilidad/",
            json={
                "idSucursal": SUCURSAL_ID,
                "nombre": "Sucursal Test",
                "idProducto": 1,
            },
            headers=headers,
        )
        assert crear.status_code == 200
        doc_id = crear.json()["id"]

        listado = client.get(f"/disponibilidad/{SUCURSAL_ID}")
        assert listado.status_code == 200
        assert listado.json()[0]["id"] == doc_id
        assert "_id" not in listado.json()[0]

        borrar = client.delete(f"/disponibilidad/{doc_id}", headers=headers)
        assert borrar.status_code == 200

    def test_obtener_por_documento_y_actualizar(self):
        client = api_client()
        headers = admin_user()
        sucursal_id = 88051
        client.post(
            "/sucursales/",
            json={"id": sucursal_id, "nombre": "Suc PUT Test", "ciudad": "Medellín"},
            headers=headers,
        )
        crear = client.post(
            "/disponibilidad/",
            json={
                "idSucursal": sucursal_id,
                "nombre": "Suc PUT Test",
                "idProducto": 2,
            },
            headers=headers,
        )
        assert crear.status_code == 200
        doc_id = crear.json()["id"]

        obtener = client.get(f"/disponibilidad/{doc_id}")
        assert obtener.status_code == 200
        assert obtener.json()["idProducto"] == 2

        actualizar = client.put(
            f"/disponibilidad/{doc_id}",
            json={
                "idSucursal": sucursal_id,
                "nombre": "Suc PUT Actualizada",
                "idProducto": 3,
            },
            headers=headers,
        )
        assert actualizar.status_code == 200

        verificado = client.get(f"/disponibilidad/{doc_id}")
        assert verificado.json()["idProducto"] == 3
        assert verificado.json()["nombre"] == "Suc PUT Actualizada"

        client.delete(f"/disponibilidad/{doc_id}", headers=headers)


class TestListado:
    def test_listar_todas(self):
        response = api_client().get("/disponibilidad/")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_sucursal_sin_disponibilidad(self):
        assert api_client().get("/disponibilidad/88888").status_code == 404

    def test_sucursal_id_invalido(self):
        assert api_client().get("/disponibilidad/abc").status_code == 404

    def test_eliminar_inexistente(self):
        oid_inexistente = "507f1f77bcf86cd799439999"
        response = api_client().delete(
            f"/disponibilidad/{oid_inexistente}",
            headers=admin_user(),
        )
        assert response.status_code == 404
