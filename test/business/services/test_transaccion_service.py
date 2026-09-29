from datetime import datetime
from unittest.mock import MagicMock

import pytest
from bson import ObjectId
from fastapi import HTTPException
from pymongo.errors import DuplicateKeyError

from app.business.services import transaccion_service
from app.persistence import (
    cliente_repository,
    inscripcion_repository,
    producto_repository,
    transaccion_repository,
)
from test.business.services.auth_test_support import cliente_user


class TestSerializeTransaccion:
    def test_convierte_object_ids_a_str(self):
        oid = ObjectId()
        tx = {
            "_id": oid,
            "idCliente": ObjectId(),
            "idProducto": ObjectId(),
            "tipo": "apertura",
        }
        result = transaccion_service.serialize_transaccion(tx)
        assert result["_id"] == str(oid)
        assert isinstance(result["idCliente"], str)
        assert isinstance(result["idProducto"], str)


class TestEjecutarApertura:
    def test_cliente_sin_saldo(self, monkeypatch):
        producto = producto_repository.find_by_id(1)
        monkeypatch.setattr(
            inscripcion_repository,
            "find_one",
            lambda _c, _p: None,
        )
        monkeypatch.setattr(
            cliente_repository,
            "find_by_id",
            lambda _id: {"id": 1, "nombre": "Sin saldo"},
        )
        monkeypatch.setattr(
            producto_repository,
            "find_by_id",
            lambda _id: producto,
        )
        with pytest.raises(HTTPException) as exc:
            transaccion_service.ejecutar_apertura_fondo(1, 1)
        assert exc.value.status_code == 400
        assert "saldo definido" in exc.value.detail.lower()

    def test_descontar_saldo_fallo(self, monkeypatch):
        user = cliente_user()
        id_cliente = user["id"]
        producto = producto_repository.find_by_id(1)
        monkeypatch.setattr(
            inscripcion_repository,
            "find_one",
            lambda _c, _p: None,
        )
        monkeypatch.setattr(
            cliente_repository,
            "find_by_id",
            lambda _id: {"id": id_cliente, "saldo": producto["monto_minimo"]},
        )
        monkeypatch.setattr(
            producto_repository,
            "find_by_id",
            lambda _id: producto,
        )
        monkeypatch.setattr(cliente_repository, "descontar_saldo", lambda _c, _m: None)
        with pytest.raises(HTTPException) as exc:
            transaccion_service.ejecutar_apertura_fondo(id_cliente, 1)
        assert exc.value.status_code == 400

    def test_inscripcion_duplicate_key_rollback(self, monkeypatch):
        user = cliente_user()
        id_cliente = user["id"]
        producto = producto_repository.find_by_id(1)
        depositos: list[int] = []

        monkeypatch.setattr(
            inscripcion_repository,
            "find_one",
            lambda _c, _p: None,
        )
        monkeypatch.setattr(
            cliente_repository,
            "find_by_id",
            lambda _id: {"id": id_cliente, "saldo": producto["monto_minimo"]},
        )
        monkeypatch.setattr(
            producto_repository,
            "find_by_id",
            lambda _id: producto,
        )
        monkeypatch.setattr(
            cliente_repository,
            "descontar_saldo",
            lambda _c, m: {"id": id_cliente, "saldo": producto["monto_minimo"] - m},
        )
        monkeypatch.setattr(
            inscripcion_repository,
            "insert",
            lambda _data: (_ for _ in ()).throw(DuplicateKeyError("dup")),
        )
        monkeypatch.setattr(
            cliente_repository,
            "depositar_saldo",
            lambda _c, m: depositos.append(m) or {"id": id_cliente, "saldo": m},
        )

        with pytest.raises(HTTPException) as exc:
            transaccion_service.ejecutar_apertura_fondo(id_cliente, 1)
        assert exc.value.status_code == 409
        assert depositos == [producto["monto_minimo"]]

    def test_inscripcion_error_generico(self, monkeypatch):
        user = cliente_user()
        id_cliente = user["id"]
        producto = producto_repository.find_by_id(1)

        monkeypatch.setattr(
            inscripcion_repository,
            "find_one",
            lambda _c, _p: None,
        )
        monkeypatch.setattr(
            cliente_repository,
            "find_by_id",
            lambda _id: {"id": id_cliente, "saldo": producto["monto_minimo"]},
        )
        monkeypatch.setattr(
            producto_repository,
            "find_by_id",
            lambda _id: producto,
        )
        monkeypatch.setattr(
            cliente_repository,
            "descontar_saldo",
            lambda _c, m: {"id": id_cliente, "saldo": 0},
        )
        monkeypatch.setattr(
            inscripcion_repository,
            "insert",
            lambda _data: (_ for _ in ()).throw(RuntimeError("db down")),
        )
        monkeypatch.setattr(
            cliente_repository,
            "depositar_saldo",
            lambda _c, _m: {"id": id_cliente, "saldo": producto["monto_minimo"]},
        )

        with pytest.raises(HTTPException) as exc:
            transaccion_service.ejecutar_apertura_fondo(id_cliente, 1)
        assert exc.value.status_code == 500
        assert "inscripción" in exc.value.detail.lower()

    def test_transaccion_fallo_apertura(self, monkeypatch):
        user = cliente_user()
        id_cliente = user["id"]
        producto = producto_repository.find_by_id(1)
        rollback: dict[str, bool] = {"inscripcion": False, "saldo": False}

        monkeypatch.setattr(
            inscripcion_repository,
            "find_one",
            lambda _c, _p: None,
        )
        monkeypatch.setattr(
            cliente_repository,
            "find_by_id",
            lambda _id: {"id": id_cliente, "saldo": producto["monto_minimo"]},
        )
        monkeypatch.setattr(
            producto_repository,
            "find_by_id",
            lambda _id: producto,
        )
        monkeypatch.setattr(
            cliente_repository,
            "descontar_saldo",
            lambda _c, m: {"id": id_cliente, "saldo": 0},
        )
        monkeypatch.setattr(inscripcion_repository, "insert", lambda _data: MagicMock())
        monkeypatch.setattr(
            transaccion_repository,
            "insert",
            lambda _data: (_ for _ in ()).throw(RuntimeError("tx fail")),
        )
        monkeypatch.setattr(
            inscripcion_repository,
            "delete",
            lambda _c, _p: rollback.update(inscripcion=True) or MagicMock(deleted_count=1),
        )
        monkeypatch.setattr(
            cliente_repository,
            "depositar_saldo",
            lambda _c, _m: rollback.update(saldo=True) or {"id": id_cliente, "saldo": _m},
        )

        with pytest.raises(HTTPException) as exc:
            transaccion_service.ejecutar_apertura_fondo(id_cliente, 1)
        assert exc.value.status_code == 500
        assert rollback["inscripcion"] is True
        assert rollback["saldo"] is True


class TestEjecutarCancelacion:
    def test_eliminar_inscripcion_sin_efecto(self, monkeypatch):
        inscripcion = {
            "idCliente": 1,
            "idProducto": 1,
            "fecha": datetime.now(),
            "tipo": "apertura",
            "monto": 1000,
        }
        monkeypatch.setattr(
            inscripcion_repository,
            "find_one",
            lambda _c, _p: inscripcion,
        )
        monkeypatch.setattr(
            cliente_repository,
            "find_by_id",
            lambda _id: {"id": 1, "saldo": 1000},
        )
        monkeypatch.setattr(
            producto_repository,
            "find_by_id",
            lambda _id: {"id": 1, "nombre": "Fondo", "monto_minimo": 1000},
        )
        monkeypatch.setattr(
            inscripcion_repository,
            "delete",
            lambda _c, _p: MagicMock(deleted_count=0),
        )
        with pytest.raises(HTTPException) as exc:
            transaccion_service.ejecutar_cancelacion_fondo(1, 1)
        assert exc.value.status_code == 404

    def test_depositar_saldo_fallo_inscripcion(self, monkeypatch):
        inscripcion = {
            "idCliente": 1,
            "idProducto": 1,
            "fecha": datetime.now(),
            "tipo": "apertura",
            "monto": 1000,
        }
        restaurada: list[dict] = []
        monkeypatch.setattr(
            inscripcion_repository,
            "find_one",
            lambda _c, _p: inscripcion,
        )
        monkeypatch.setattr(
            cliente_repository,
            "find_by_id",
            lambda _id: {"id": 1, "saldo": 1000},
        )
        monkeypatch.setattr(
            producto_repository,
            "find_by_id",
            lambda _id: {"id": 1, "nombre": "Fondo", "monto_minimo": 1000},
        )
        monkeypatch.setattr(
            inscripcion_repository,
            "delete",
            lambda _c, _p: MagicMock(deleted_count=1),
        )
        monkeypatch.setattr(cliente_repository, "depositar_saldo", lambda _c, _m: None)
        monkeypatch.setattr(
            inscripcion_repository,
            "insert",
            lambda data: restaurada.append(data) or MagicMock(),
        )
        with pytest.raises(HTTPException) as exc:
            transaccion_service.ejecutar_cancelacion_fondo(1, 1)
        assert exc.value.status_code == 404
        assert len(restaurada) == 1

    def test_transaccion_fallo_cancelacion(self, monkeypatch):
        inscripcion = {
            "idCliente": 1,
            "idProducto": 1,
            "fecha": datetime.now(),
            "tipo": "apertura",
            "monto": 1000,
        }
        rollback: dict[str, bool] = {"inscripcion": False, "saldo": False}
        monkeypatch.setattr(
            inscripcion_repository,
            "find_one",
            lambda _c, _p: inscripcion,
        )
        monkeypatch.setattr(
            cliente_repository,
            "find_by_id",
            lambda _id: {"id": 1, "saldo": 1000},
        )
        monkeypatch.setattr(
            producto_repository,
            "find_by_id",
            lambda _id: {"id": 1, "nombre": "Fondo", "monto_minimo": 1000},
        )
        monkeypatch.setattr(
            inscripcion_repository,
            "delete",
            lambda _c, _p: MagicMock(deleted_count=1),
        )
        monkeypatch.setattr(
            cliente_repository,
            "depositar_saldo",
            lambda _c, _m: {"id": 1, "saldo": 2000},
        )
        monkeypatch.setattr(
            transaccion_repository,
            "insert",
            lambda _data: (_ for _ in ()).throw(RuntimeError("tx fail")),
        )
        monkeypatch.setattr(
            cliente_repository,
            "descontar_saldo",
            lambda _c, _m: rollback.update(saldo=True) or {"id": 1, "saldo": 1000},
        )
        monkeypatch.setattr(
            inscripcion_repository,
            "insert",
            lambda _data: rollback.update(inscripcion=True) or MagicMock(),
        )
        with pytest.raises(HTTPException) as exc:
            transaccion_service.ejecutar_cancelacion_fondo(1, 1)
        assert exc.value.status_code == 500
        assert rollback["inscripcion"] is True
        assert rollback["saldo"] is True


class TestObtenerHistorial:
    def test_token_sin_cliente_identificable(self):
        with pytest.raises(HTTPException) as exc:
            transaccion_service.obtener_historial(
                {
                    "rol": "cliente",
                    "user_id": "507f1f77bcf86cd799439011",
                    "cliente_id": None,
                }
            )
        assert exc.value.status_code == 403
