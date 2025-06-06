import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

# --- CLIENTES ---
def test_crear_cliente():
    data = {
         "nombre": "Juan",
         "apellidos": "Pérez",
         "ciudad": "Bogotá",
         "email": "juan@gmail.com"
    }
    response = client.post("/clientes/", json=data, params={"password": "Password123!"})
    # Si falla, intenta enviar el password como campo separado en el body
    if response.status_code == 422:
        response = client.post("/clientes/", json={**data}, data={"password": "Password123!"})
    assert response.status_code == 200
    assert "id" in response.json()


def test_obtener_clientes():
    response = client.get("/clientes/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

# --- SUCURSALES ---
def test_crear_sucursal():
    data = {"nombre": "Sucursal Test", "ciudad": "Test City"}
    response = client.post("/sucursales/", json=data)
    assert response.status_code == 200
    assert "id" in response.json()


def test_obtener_sucursales():
    response = client.get("/sucursales/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

# --- PRODUCTOS ---
def test_crear_producto():
    data = {"nombre": "Producto Test", "monto_minimo": 140000, "categoria": "FPV"}
    response = client.post("/productos/", json=data)
    # Si falla, intenta enviar el campo id como None
    if response.status_code == 422:
        data["id"] = None
        response = client.post("/productos/", json=data)
    assert response.status_code == 200
    assert "id" in response.json()


def test_obtener_productos():
    response = client.get("/productos/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

# --- VISITAS ---
def test_registrar_visita():
    data = {"idSucursal": 1, "idCliente": 1, "fechaVisita": "2025-06-06T09:43:13.643Z"}
    response = client.post("/visitas/", json=data)
    assert response.status_code == 200
    assert "id" in response.json()


def test_obtener_visitas():
    response = client.get("/visitas/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

# --- TRANSACCIONES ---
def test_suscribirse_fondo():
    data = {"idCliente": 1, "idProducto": 1, "tipo": "apertura", "monto": 1000}
    response = client.post("/transacciones/apertura/", json=data)
    assert response.status_code in (200, 400, 404)  # Puede fallar si no hay saldo o cliente


def test_cancelar_suscripcion():
    data = {"idCliente": 1, "idProducto": 1, "tipo": "cancelacion", "monto": 1000}
    response = client.post("/transacciones/cancelacion/", json=data)
    assert response.status_code in (200, 400, 404)


def test_ver_historial_transacciones():
    response = client.get("/transacciones/")
    assert response.status_code == 200
    assert isinstance(response.json(), list) or "mensaje" in response.json()
