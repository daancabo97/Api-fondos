from fastapi.testclient import TestClient

import test.database.test_env  # noqa: F401  — fija DATABASE_NAME antes de importar app
from app.main import app

_test_client: TestClient | None = None


def api_client() -> TestClient:
    global _test_client
    if _test_client is None:
        _test_client = TestClient(app)
    return _test_client
