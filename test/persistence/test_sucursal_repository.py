"""Tests — app.persistence.sucursal_repository."""
import pytest

from app.persistence import sucursal_repository
from test.business.services.auth_test_support import admin_user
from test.presentation.api_client import api_client


class TestFindByPathId:
    def test_por_id_numerico(self):
        temp_id = 99004
        client = api_client()
        headers = admin_user()
        client.post(
            "/sucursales/",
            json={"id": temp_id, "nombre": "Suc Repo Test", "ciudad": "Cali"},
            headers=headers,
        )
        found = sucursal_repository.find_by_path_id(str(temp_id))
        assert found is not None
        assert found["nombre"] == "Suc Repo Test"

    def test_por_object_id(self):
        temp_id = 99005
        client = api_client()
        headers = admin_user()
        crear = client.post(
            "/sucursales/",
            json={"id": temp_id, "nombre": "Suc OID Test", "ciudad": "Barranquilla"},
            headers=headers,
        )
        assert crear.status_code == 200
        oid = crear.json()["id"]
        found = sucursal_repository.find_by_path_id(oid)
        assert found is not None
        assert found["id"] == temp_id

    def test_object_id_invalido(self):
        assert sucursal_repository.find_by_path_id("no-valido") is None


class TestFindByObjectId:
    def test_encuentra_documento(self):
        temp_id = 99006
        client = api_client()
        headers = admin_user()
        crear = client.post(
            "/sucursales/",
            json={"id": temp_id, "nombre": "Suc Direct OID", "ciudad": "Pereira"},
            headers=headers,
        )
        oid = crear.json()["id"]
        found = sucursal_repository.find_by_object_id(oid)
        assert found is not None
        assert found["nombre"] == "Suc Direct OID"

    def test_object_id_malformado_lanza(self):
        with pytest.raises(Exception):
            sucursal_repository.find_by_object_id("malformado")
