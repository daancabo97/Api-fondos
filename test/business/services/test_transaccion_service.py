import asyncio
import logging
from datetime import datetime
from unittest.mock import MagicMock

import pytest
from bson import ObjectId
from fastapi import HTTPException
from pymongo.errors import DuplicateKeyError

from app.business.services import notificaciones_service, transaccion_service
from app.persistence import (
    cliente_repository,
    inscripcion_repository,
    producto_repository,
    transaccion_repository,
)
from test.business.services.auth_test_support import cliente_user
from test.business.services.test_notificaciones import (
    limpiar_mensajes_email,
    mensajes_email,
)


def _forzar_mongo_sin_sesion(monkeypatch):
    """Estas pruebas comprueban el deshacer a mano, no el rollback del replica set."""
    monkeypatch.setattr(
        "app.database.transactions.mongo_supports_transactions",
        lambda: False,
    )


class TestSerializeTransaccion:
    def test_serializar_transaccion_convierte_object_id_a_texto(self):
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
    def test_apertura_rechaza_cliente_sin_saldo_definido(self, monkeypatch):
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
            asyncio.run(transaccion_service.ejecutar_apertura_fondo(1, 1))
        assert exc.value.status_code == 400
        assert "saldo definido" in exc.value.detail.lower()

    def test_apertura_rechaza_cuando_el_debito_no_aplica(self, monkeypatch):
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
            lambda _c, _m, session=None: None,
        )
        with pytest.raises(HTTPException) as exc:
            asyncio.run(transaccion_service.ejecutar_apertura_fondo(id_cliente, 1))
        assert exc.value.status_code == 400

    def test_apertura_revierte_saldo_si_la_inscripcion_ya_existe(self, monkeypatch):
        _forzar_mongo_sin_sesion(monkeypatch)
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
            lambda _c, m, session=None: {
                "id": id_cliente,
                "saldo": producto["monto_minimo"] - m,
            },
        )
        monkeypatch.setattr(
            inscripcion_repository,
            "insert",
            lambda _data, session=None: (_ for _ in ()).throw(DuplicateKeyError("dup")),
        )
        monkeypatch.setattr(
            cliente_repository,
            "depositar_saldo",
            lambda _c, m, session=None: depositos.append(m) or {"id": id_cliente, "saldo": m},
        )

        with pytest.raises(HTTPException) as exc:
            asyncio.run(transaccion_service.ejecutar_apertura_fondo(id_cliente, 1))
        assert exc.value.status_code == 409
        assert depositos == [producto["monto_minimo"]]

    def test_apertura_revierte_saldo_si_falla_el_registro_de_inscripcion(self, monkeypatch):
        _forzar_mongo_sin_sesion(monkeypatch)
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
            lambda _c, m, session=None: {"id": id_cliente, "saldo": 0},
        )
        monkeypatch.setattr(
            inscripcion_repository,
            "insert",
            lambda _data, session=None: (_ for _ in ()).throw(RuntimeError("db down")),
        )
        monkeypatch.setattr(
            cliente_repository,
            "depositar_saldo",
            lambda _c, _m, session=None: {
                "id": id_cliente,
                "saldo": producto["monto_minimo"],
            },
        )

        with pytest.raises(HTTPException) as exc:
            asyncio.run(transaccion_service.ejecutar_apertura_fondo(id_cliente, 1))
        assert exc.value.status_code == 500
        assert "inscripción" in exc.value.detail.lower()

    def test_apertura_revierte_saldo_e_inscripcion_si_falla_la_transaccion(self, monkeypatch):
        _forzar_mongo_sin_sesion(monkeypatch)
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
            lambda _c, m, session=None: {"id": id_cliente, "saldo": 0},
        )
        monkeypatch.setattr(
            inscripcion_repository,
            "insert",
            lambda _data, session=None: MagicMock(),
        )
        monkeypatch.setattr(
            transaccion_repository,
            "insert",
            lambda _data, session=None: (_ for _ in ()).throw(RuntimeError("tx fail")),
        )
        monkeypatch.setattr(
            inscripcion_repository,
            "delete",
            lambda _c, _p, session=None: (
                rollback.update(inscripcion=True) or MagicMock(deleted_count=1)
            ),
        )
        monkeypatch.setattr(
            cliente_repository,
            "depositar_saldo",
            lambda _c, _m, session=None: (
                rollback.update(saldo=True) or {"id": id_cliente, "saldo": _m}
            ),
        )

        with pytest.raises(HTTPException) as exc:
            asyncio.run(transaccion_service.ejecutar_apertura_fondo(id_cliente, 1))
        assert exc.value.status_code == 500
        assert rollback["inscripcion"] is True
        assert rollback["saldo"] is True

    def test_con_sesion_de_mongo_no_deshace_el_saldo_a_mano(self, monkeypatch):
        user = cliente_user()
        id_cliente = user["id"]
        producto = producto_repository.find_by_id(1)
        depositos: list[int] = []

        class _SesionMongo:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def with_transaction(self, funcion):
                return funcion(self)

        monkeypatch.setattr(
            "app.database.transactions.mongo_supports_transactions",
            lambda: True,
        )
        monkeypatch.setattr(
            "app.database.transactions.client.start_session",
            lambda: _SesionMongo(),
        )
        monkeypatch.setattr(inscripcion_repository, "find_one", lambda _c, _p: None)
        monkeypatch.setattr(
            cliente_repository,
            "find_by_id",
            lambda _id: {"id": id_cliente, "saldo": producto["monto_minimo"]},
        )
        monkeypatch.setattr(producto_repository, "find_by_id", lambda _id: producto)
        monkeypatch.setattr(
            cliente_repository,
            "descontar_saldo",
            lambda _c, m, session=None: {
                "id": id_cliente,
                "saldo": producto["monto_minimo"] - m,
            },
        )
        monkeypatch.setattr(
            inscripcion_repository,
            "insert",
            lambda _data, session=None: (_ for _ in ()).throw(DuplicateKeyError("dup")),
        )
        monkeypatch.setattr(
            cliente_repository,
            "depositar_saldo",
            lambda _c, m, session=None: depositos.append(m) or {"id": id_cliente, "saldo": m},
        )

        with pytest.raises(HTTPException) as exc:
            asyncio.run(transaccion_service.ejecutar_apertura_fondo(id_cliente, 1))
        assert exc.value.status_code == 409
        assert depositos == []


class TestEjecutarCancelacion:
    def test_cancelacion_rechaza_cuando_la_inscripcion_no_se_elimina(self, monkeypatch):
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
            lambda _c, _p, session=None: MagicMock(deleted_count=0),
        )
        with pytest.raises(HTTPException) as exc:
            asyncio.run(transaccion_service.ejecutar_cancelacion_fondo(1, 1))
        assert exc.value.status_code == 404

    def test_cancelacion_restaura_inscripcion_si_falla_el_reintegro(self, monkeypatch):
        _forzar_mongo_sin_sesion(monkeypatch)
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
            lambda _c, _p, session=None: MagicMock(deleted_count=1),
        )
        monkeypatch.setattr(
            cliente_repository,
            "depositar_saldo",
            lambda _c, _m, session=None: None,
        )
        monkeypatch.setattr(
            inscripcion_repository,
            "insert",
            lambda data, session=None: restaurada.append(data) or MagicMock(),
        )
        with pytest.raises(HTTPException) as exc:
            asyncio.run(transaccion_service.ejecutar_cancelacion_fondo(1, 1))
        assert exc.value.status_code == 404
        assert len(restaurada) == 1

    def test_cancelacion_revierte_reintegro_e_inscripcion_si_falla_transaccion(self, monkeypatch):
        _forzar_mongo_sin_sesion(monkeypatch)
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
            lambda _c, _p, session=None: MagicMock(deleted_count=1),
        )
        monkeypatch.setattr(
            cliente_repository,
            "depositar_saldo",
            lambda _c, _m, session=None: {"id": 1, "saldo": 2000},
        )
        monkeypatch.setattr(
            transaccion_repository,
            "insert",
            lambda _data, session=None: (_ for _ in ()).throw(RuntimeError("tx fail")),
        )
        monkeypatch.setattr(
            cliente_repository,
            "descontar_saldo",
            lambda _c, _m, session=None: (
                rollback.update(saldo=True) or {"id": 1, "saldo": 1000}
            ),
        )
        monkeypatch.setattr(
            inscripcion_repository,
            "insert",
            lambda _data, session=None: rollback.update(inscripcion=True) or MagicMock(),
        )
        with pytest.raises(HTTPException) as exc:
            asyncio.run(transaccion_service.ejecutar_cancelacion_fondo(1, 1))
        assert exc.value.status_code == 500
        assert rollback["inscripcion"] is True
        assert rollback["saldo"] is True


class TestObtenerHistorial:
    def test_historial_rechaza_token_sin_cliente(self):
        with pytest.raises(HTTPException) as exc:
            transaccion_service.obtener_historial_transaccion(
                {
                    "rol": "cliente",
                    "user_id": "507f1f77bcf86cd799439011",
                    "cliente_id": None,
                }
            )
        assert exc.value.status_code == 403


def _simular_suscripcion_de_fondo(monkeypatch, email: str, telefono: str, *, suscrito: bool):
    producto = {
        "id": 1,
        "nombre": "FPV_BTG_PACTUAL_RECAUDADORA",
        "monto_minimo": 75000,
    }
    cliente = {
        "id": 1,
        "saldo": 500000,
        "email": email,
        "telefono": telefono,
    }
    inscripcion = None
    if suscrito:
        inscripcion = {
            "idCliente": 1,
            "idProducto": 1,
            "fecha": datetime.now(),
            "tipo": "apertura",
            "monto": 75000,
        }
    actualizado = {**cliente, "saldo": 425000}

    monkeypatch.setattr(inscripcion_repository, "find_one", lambda _c, _p: inscripcion)
    monkeypatch.setattr(cliente_repository, "find_by_id", lambda _id: cliente)
    monkeypatch.setattr(producto_repository, "find_by_id", lambda _id: producto)
    monkeypatch.setattr(
        cliente_repository,
        "descontar_saldo",
        lambda _c, _m, session=None: actualizado,
    )
    monkeypatch.setattr(
        cliente_repository,
        "depositar_saldo",
        lambda _c, _m, session=None: actualizado,
    )
    monkeypatch.setattr(
        inscripcion_repository,
        "insert",
        lambda _data, session=None: MagicMock(),
    )
    monkeypatch.setattr(
        inscripcion_repository,
        "delete",
        lambda _c, _p, session=None: MagicMock(deleted_count=1),
    )
    monkeypatch.setattr(
        transaccion_repository,
        "insert",
        lambda _data, session=None: MagicMock(),
    )
    return producto


def _registrar_envios_sms(monkeypatch) -> list[dict]:
    enviados: list[dict] = []

    async def fake_sms(destinatario: str, mensaje: str) -> None:
        enviados.append({"destinatario": destinatario, "mensaje": mensaje})

    monkeypatch.setattr(notificaciones_service, "_twilio_configurado", lambda: True)
    monkeypatch.setattr(notificaciones_service, "_enviar_sms_twilio", fake_sms)
    return enviados


class TestNotificacionDeFondo:
    def test_apertura_notifica_el_mismo_mensaje_por_email_y_sms(self, monkeypatch):
        email = "cliente@fondos360.com"
        telefono = "+573001112233"
        producto = _simular_suscripcion_de_fondo(
            monkeypatch, email, telefono, suscrito=False
        )
        sms = _registrar_envios_sms(monkeypatch)
        limpiar_mensajes_email()

        respuesta = asyncio.run(
            transaccion_service.ejecutar_apertura_fondo(1, 1, avisar_operacion_sms_email=True)
        )

        cuerpo = (
            f"Te has suscrito al fondo {producto['nombre']} "
            f"con un monto de {producto['monto_minimo']}. "
            f"ID transacción: {respuesta['transaccion_id']}"
        )
        assert respuesta["mensaje"] == cuerpo
        assert mensajes_email == [
            {"subject": "Suscripción Exitosa", "recipients": [email], "body": cuerpo}
        ]
        assert sms == [{"destinatario": telefono, "mensaje": cuerpo}]

    def test_cancelacion_notifica_el_mismo_mensaje_por_email_y_sms(self, monkeypatch):
        email = "cliente@fondos360.com"
        telefono = "+573001112233"
        producto = _simular_suscripcion_de_fondo(
            monkeypatch, email, telefono, suscrito=True
        )
        sms = _registrar_envios_sms(monkeypatch)
        limpiar_mensajes_email()

        respuesta = asyncio.run(
            transaccion_service.ejecutar_cancelacion_fondo(1, 1, avisar_operacion_sms_email=True)
        )

        cuerpo = (
            f"Has cancelado tu suscripción al fondo {producto['nombre']}. "
            f"ID transacción: {respuesta['transaccion_id']}"
        )
        assert respuesta["mensaje"] == cuerpo
        assert mensajes_email == [
            {
                "subject": "Cancelación de Suscripción",
                "recipients": [email],
                "body": cuerpo,
            }
        ]
        assert sms == [{"destinatario": telefono, "mensaje": cuerpo}]

    def test_apertura_sin_telefono_notifica_solo_por_email(self, monkeypatch):
        email = "cliente@fondos360.com"
        _simular_suscripcion_de_fondo(monkeypatch, email, "", suscrito=False)
        sms = _registrar_envios_sms(monkeypatch)
        limpiar_mensajes_email()

        asyncio.run(
            transaccion_service.ejecutar_apertura_fondo(1, 1, avisar_operacion_sms_email=True)
        )

        assert mensajes_email[0]["recipients"] == [email]
        assert mensajes_email[0]["subject"] == "Suscripción Exitosa"
        assert sms == []

    def test_un_canal_fallido_no_cancela_el_otro(self, monkeypatch, caplog):
        enviados: list[str] = []

        async def email_falla(_evento):
            raise RuntimeError("smtp caido")

        async def sms_ok(_evento):
            enviados.append("sms")

        monkeypatch.setattr(transaccion_service, "notificar_por_email", email_falla)
        monkeypatch.setattr(transaccion_service, "notificar_por_sms", sms_ok)
        with caplog.at_level(logging.ERROR):
            asyncio.run(
                transaccion_service._launch_notification_observers(
                    {
                        "email": "cliente@fondos360.com",
                        "telefono": "+573001112233",
                        "asunto": "Suscripción Exitosa",
                        "mensaje": "Aviso",
                    }
                )
            )
        assert enviados == ["sms"]
        assert "smtp caido" in caplog.text
