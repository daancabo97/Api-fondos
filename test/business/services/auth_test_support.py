from app.business.services import auth_service
from app.persistence import cliente_repository, sequence_repository
from test.presentation.api_client import api_client

ADMIN_EMAIL = "admin.fondos360@gmail.com"
CLIENTE_EMAIL = "cliente.fondos360@gmail.com"
PASSWORD = "Password123*"


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def auth_headers_for_email(email: str) -> dict:
    """JWT directo — evita rate-limit de POST /login en la suite."""
    cliente = cliente_repository.find_by_email(email)
    assert cliente, f"Cliente {email} no encontrado para tests"
    token = auth_service.create_access_token(
        {
            "sub": str(cliente["_id"]),
            "rol": cliente.get("rol", "cliente"),
            "cliente_id": cliente.get("id"),
        }
    )
    return _auth_headers(token)


def ensure_admin_user() -> None:
    existing = cliente_repository.find_by_email(ADMIN_EMAIL)
    cliente_id = existing["id"] if existing else sequence_repository.get_next_client_id()
    cliente_repository.upsert_by_email(
        ADMIN_EMAIL,
        {
            "nombre": "Carlos",
            "apellidos": "García",
            "ciudad": "Bogota",
            "saldo": 500000,
            "email": ADMIN_EMAIL,
            "rol": "admin",
            "password": auth_service.get_password_hash(PASSWORD),
            "telefono": "+573009999999",
            "canal_notificacion": "email",
            "id": cliente_id,
        },
    )


def admin_user() -> dict:
    """Headers JWT de admin — app.presentation.dependencies.require_admin."""
    ensure_admin_user()
    return auth_headers_for_email(ADMIN_EMAIL)


def cliente_user() -> dict:
    """Headers JWT + id de cliente de prueba — routers autenticados como cliente."""
    client = api_client()
    existing = cliente_repository.find_by_email(CLIENTE_EMAIL)
    if not existing:
        response = client.post(
            "/clientes/",
            json={
                "cliente": {
                    "nombre": "Juan",
                    "apellidos": "Pérez",
                    "ciudad": "Bogotá",
                    "saldo": 500000,
                    "email": CLIENTE_EMAIL,
                    "telefono": "+573001234567",
                    "canal_notificacion": "email",
                },
                "password": PASSWORD,
            },
        )
        assert response.status_code == 200, response.text
        cliente_id = response.json()["id"]
    else:
        cliente_id = existing["id"]

    headers = auth_headers_for_email(CLIENTE_EMAIL)
    return {"headers": headers, "id": cliente_id, "email": CLIENTE_EMAIL}
