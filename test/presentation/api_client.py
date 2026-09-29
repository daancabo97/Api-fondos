from fastapi.testclient import TestClient

import test.database.test_env
from app.main import app

_test_client: TestClient | None = None


def api_client() -> TestClient:
    global _test_client
    if _test_client is None:
        _test_client = TestClient(app)
    return _test_client
