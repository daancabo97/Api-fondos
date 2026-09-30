import asyncio

from app.business.services import notificaciones_service
from test.business.services.test_notificaciones import (
    limpiar_mensajes_email,
    mensajes_email,
)


def _event_notification_service(**extra) -> dict:
    evento = {
        "email": "",
        "telefono": "",
        "asunto": "Asunto",
        "mensaje": "Cuerpo",
    }
    evento.update(extra)
    return evento


class TestObservadores:
    def test_notificar_por_email_con_correo(self):
        limpiar_mensajes_email()
        asyncio.run(
            notificaciones_service.notificar_por_email(
                _event_notification_service(
                    email="test@gmail.com",
                    telefono="+573009999999",
                    asunto="Suscripción Exitosa",
                    mensaje="Te has suscrito al fondo Fondo Demo.",
                )
            )
        )
        assert mensajes_email == [
            {
                "subject": "Suscripción Exitosa",
                "recipients": ["test@gmail.com"],
                "body": "Te has suscrito al fondo Fondo Demo.",
            }
        ]

    def test_notificar_por_email_sin_correo(self):
        limpiar_mensajes_email()
        asyncio.run(
            notificaciones_service.notificar_por_email(
                _event_notification_service(
                    telefono="+573009999999",
                    asunto="Suscripción Exitosa",
                    mensaje="Te has suscrito al fondo Fondo Demo.",
                )
            )
        )
        assert mensajes_email == []

    def test_notificar_por_sms_con_telefono(self, caplog):
        import logging

        with caplog.at_level(logging.INFO):
            asyncio.run(
                notificaciones_service.notificar_por_sms(
                    _event_notification_service(
                        email="test@gmail.com",
                        telefono="+573009999999",
                        mensaje="Te has suscrito al fondo Fondo Demo.",
                    )
                )
            )
        assert any(
            "[SMS simulado]" in r.message
            and "+573009999999" in r.message
            and "Te has suscrito al fondo Fondo Demo." in r.message
            for r in caplog.records
        )

    def test_notificar_por_sms_sin_telefono(self, caplog):
        import logging

        with caplog.at_level(logging.INFO):
            asyncio.run(
                notificaciones_service.notificar_por_sms(
                    _event_notification_service(email="test@gmail.com")
                )
            )
        assert not any("[SMS simulado]" in r.message for r in caplog.records)
