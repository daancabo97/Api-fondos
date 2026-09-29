"""Paquete de tests — espejo de app/ (presentation, business, persistence, database)."""
import test.database.test_env  # noqa: F401 — BTG_test antes de importar app
from test.business.services.test_notificaciones import aplicar_mock
from test.persistence.test_catalogo_fondos import cargar_catalogo_fondos

aplicar_mock()
cargar_catalogo_fondos()
