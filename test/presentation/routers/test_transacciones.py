import uuid

from test.business.services.auth_test_support import (
    admin_user,
    auth_headers_for_email,
    cliente_user,
)
from test.presentation.api_client import api_client


class TestApertura:
    def test_suscribirse_fondo(self):
        user = cliente_user()
        body = {"idCliente": user["id"], "idProducto": 1}
        client = api_client()
        client.post("/transacciones/cancelacion/", json=body, headers=user["headers"])
        response = client.post(
            "/transacciones/apertura/",
            json=body,
            headers=user["headers"],
        )
        assert response.status_code == 200
        payload = response.json()
        assert "transaccion_id" in payload
        assert "mensaje" in payload

    def test_doble_apertura_rechazada(self):
        user = cliente_user()
        id_cliente = user["id"]
        headers = user["headers"]
        body = {"idCliente": id_cliente, "idProducto": 3}
        client = api_client()

        client.post("/transacciones/cancelacion/", json=body, headers=headers)

        primera = client.post("/transacciones/apertura/", json=body, headers=headers)
        assert primera.status_code == 200

        segunda = client.post("/transacciones/apertura/", json=body, headers=headers)
        assert segunda.status_code == 409
        assert "suscrito" in segunda.json()["detail"].lower()

    def test_saldo_insuficiente(self):
        user = cliente_user()
        id_cliente = user["id"]
        headers = user["headers"]
        admin_headers = admin_user()
        client = api_client()

        client.post(
            "/transacciones/cancelacion/",
            json={"idCliente": id_cliente, "idProducto": 4},
            headers=headers,
        )
        client.put(f"/clientes/{id_cliente}?nuevo_saldo=1000", headers=admin_headers)

        response = client.post(
            "/transacciones/apertura/",
            json={"idCliente": id_cliente, "idProducto": 4},
            headers=headers,
        )
        assert response.status_code == 400
        detail = response.json()["detail"]
        assert "No tiene saldo disponible para vincularse al fondo FDO-ACCIONES" in detail

        client.put(f"/clientes/{id_cliente}?nuevo_saldo=500000", headers=admin_headers)

    def test_producto_inexistente(self):
        user = cliente_user()
        response = api_client().post(
            "/transacciones/apertura/",
            json={"idCliente": user["id"], "idProducto": 99999},
            headers=user["headers"],
        )
        assert response.status_code == 404

    def test_cliente_inexistente_admin(self):
        response = api_client().post(
            "/transacciones/apertura/",
            json={"idCliente": 99999999, "idProducto": 1},
            headers=admin_user(),
        )
        assert response.status_code == 404


class TestCancelacion:
    def test_cancelar_suscripcion(self):
        user = cliente_user()
        body = {"idCliente": user["id"], "idProducto": 1}
        response = api_client().post(
            "/transacciones/cancelacion/",
            json=body,
            headers=user["headers"],
        )
        assert response.status_code in (200, 404)

    def test_flujo_apertura_y_cancelacion(self):
        user = cliente_user()
        id_cliente = user["id"]
        headers = user["headers"]
        client = api_client()

        apertura = client.post(
            "/transacciones/apertura/",
            json={"idCliente": id_cliente, "idProducto": 1},
            headers=headers,
        )
        assert apertura.status_code == 200
        assert apertura.json()["transaccion_id"] is not None
        assert "Te has suscrito al fondo FPV_BTG_PACTUAL_RECAUDADORA" in apertura.json()["mensaje"]

        cancelacion = client.post(
            "/transacciones/cancelacion/",
            json={"idCliente": id_cliente, "idProducto": 1},
            headers=headers,
        )
        assert cancelacion.status_code == 200
        assert cancelacion.json()["transaccion_id"] is not None

    def test_cancelacion_sin_suscripcion_previa(self):
        user = cliente_user()
        body = {"idCliente": user["id"], "idProducto": 2}
        client = api_client()
        client.post("/transacciones/cancelacion/", json=body, headers=user["headers"])

        response = client.post("/transacciones/cancelacion/", json=body, headers=user["headers"])
        assert response.status_code == 404
        assert "suscrito" in response.json()["detail"].lower()


class TestNotificacion:
    def test_apertura_sin_contacto_notifica_mensaje(self):
        email = f"sin.mail.{uuid.uuid4().hex[:8]}@gmail.com"
        client = api_client()
        reg = client.post(
            "/clientes/",
            json={
                "cliente": {
                    "nombre": "Sin",
                    "apellidos": "Mail",
                    "ciudad": "Bogotá",
                    "saldo": 500000,
                    "email": email,
                    "telefono": "+573001111111",                },
                "password": "Password123*",
            },
        )
        assert reg.status_code == 200
        id_cliente = reg.json()["id"]
        headers = auth_headers_for_email(email)

        from app.persistence import cliente_repository


        cliente_repository._collection.update_one(
            {"email": email},
            {"$set": {"telefono": ""}},
        )

        body = {"idCliente": id_cliente, "idProducto": 5}
        client.post("/transacciones/cancelacion/", json=body, headers=headers)
        response = client.post("/transacciones/apertura/", json=body, headers=headers)
        assert response.status_code == 200
        notif = response.json()["notificacion"]
        assert "enviada por email" in notif.lower()
        assert "No se encontró contacto" in notif
        assert "sms" in notif.lower()


class TestHistorial:
    def test_ver_historial_transacciones(self):
        user = cliente_user()
        response = api_client().get("/transacciones/", headers=user["headers"])
        assert response.status_code == 200

    def test_historial_vacio_es_lista(self):
        email = f"sin.tx.{uuid.uuid4().hex[:8]}@gmail.com"
        client = api_client()
        client.post(
            "/clientes/",
            json={
                "cliente": {
                    "nombre": "Sin",
                    "apellidos": "Tx",
                    "ciudad": "Bogotá",
                    "saldo": 100000,
                    "email": email,
                    "telefono": "+573008888888",                },
                "password": "Password123*",
            },
        )

        response = client.get("/transacciones/", headers=auth_headers_for_email(email))
        assert response.status_code == 200
        assert response.json() == []

    def test_historial_filtro_por_tipo(self):
        user = cliente_user()
        client = api_client()
        body = {"idCliente": user["id"], "idProducto": 2}
        client.post("/transacciones/cancelacion/", json=body, headers=user["headers"])
        client.post("/transacciones/apertura/", json=body, headers=user["headers"])

        response = client.get(
            "/transacciones/?tipo=apertura",
            headers=user["headers"],
        )
        assert response.status_code == 200
        assert all(t.get("tipo") == "apertura" for t in response.json())
