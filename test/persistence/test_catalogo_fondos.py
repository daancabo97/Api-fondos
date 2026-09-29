from app.business.services import producto_service
from app.persistence import producto_repository
from test.business.services.auth_test_support import (
    ADMIN_EMAIL,
    auth_headers_for_email,
    ensure_admin_user,
)
from test.presentation.api_client import api_client


def cargar_catalogo_fondos() -> None:
    """Admin crea FONDOS_OFICIALES — mismo flujo que producción."""
    ensure_admin_user()
    client = api_client()
    headers = auth_headers_for_email(ADMIN_EMAIL)
    for fondo in producto_service.FONDOS_OFICIALES:
        if producto_repository.find_by_id(fondo["id"]):
            continue
        response = client.post("/productos/", json=fondo, headers=headers)
        assert response.status_code == 200, response.text
