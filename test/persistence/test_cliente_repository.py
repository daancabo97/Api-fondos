"""Tests — app.persistence.cliente_repository."""
import uuid
from unittest.mock import patch

import pytest
from pymongo.errors import OperationFailure

from app.persistence import cliente_repository
from test.business.services.auth_test_support import cliente_user
from test.presentation.api_client import api_client


class TestEnsureIndexes:
    def test_operation_failure_propaga(self):
        with patch.object(
            cliente_repository._collection,
            "create_index",
            side_effect=OperationFailure("idx exists"),
        ):
            with pytest.raises(OperationFailure):
                cliente_repository.ensure_indexes()


class TestFindByPathId:
    def test_por_object_id(self):
        user = cliente_user()
        cliente = cliente_repository.find_by_email(user["email"])
        oid = str(cliente["_id"])
        found = cliente_repository.find_by_path_id(oid)
        assert found is not None
        assert found["email"] == user["email"]

    def test_object_id_invalido(self):
        assert cliente_repository.find_by_path_id("no-es-object-id") is None


class TestFindByObjectId:
    def test_object_id_invalido(self):
        assert cliente_repository.find_by_object_id("invalido") is None


class TestUpdateSaldoById:
    def test_cliente_inexistente(self):
        assert cliente_repository.update_saldo_by_id(99999999, 1000) is None

    def test_actualiza_saldo(self):
        email = f"saldo.repo.{uuid.uuid4().hex[:8]}@gmail.com"
        client = api_client()
        reg = client.post(
            "/clientes/",
            json={
                "cliente": {
                    "nombre": "Saldo",
                    "apellidos": "Repo",
                    "ciudad": "Bogotá",
                    "saldo": 100000,
                    "email": email,
                    "telefono": "+573006666666",                },
                "password": "Password123*",
            },
        )
        assert reg.status_code == 200
        cid = reg.json()["id"]
        result = cliente_repository.update_saldo_by_id(cid, 250000)
        assert result is not None
        assert result.modified_count == 1
        assert cliente_repository.find_by_id(cid)["saldo"] == 250000
