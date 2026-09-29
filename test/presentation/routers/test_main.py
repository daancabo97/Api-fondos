"""Tests — app.main (/, /health)."""
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from app.main import app
from test.presentation.api_client import api_client


class TestLifespan:
    def test_startup_indexes(self):
        with TestClient(app) as client:
            assert client.get("/health").status_code == 200


class TestRoot:
    def test_root(self):
        response = api_client().get("/")
        assert response.status_code == 200


class TestHealth:
    def test_health_mongodb(self):
        response = api_client().get("/health")
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "ok"
        assert body["mongodb"] == "connected"

    def test_health_mongodb_desconectado(self, monkeypatch):
        mock_client = MagicMock()
        mock_client.admin.command.side_effect = Exception("connection refused")
        monkeypatch.setattr("app.main.mongo_client", mock_client)

        response = api_client().get("/health")
        assert response.status_code == 503
        assert response.json()["mongodb"] == "disconnected"
