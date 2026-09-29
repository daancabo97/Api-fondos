import asyncio

from app.business.services import notificaciones_service


class TestObtenerCanalContacto:
    def test_canal_email(self):
        canal, contacto = notificaciones_service.obtener_canal_contacto_notificacion(
            {"canal_notificacion": "email", "email": "a@gmail.com"}
        )
        assert canal == "email"
        assert contacto == "a@gmail.com"

    def test_canal_sms(self):
        canal, contacto = notificaciones_service.obtener_canal_contacto_notificacion(
            {"canal_notificacion": "sms", "telefono": "+573001111111"}
        )
        assert canal == "sms"
        assert contacto == "+573001111111"

    def test_sms_sin_telefono(self):
        canal, contacto = notificaciones_service.obtener_canal_contacto_notificacion(
            {"canal_notificacion": "sms"}
        )
        assert canal is None
        assert contacto is None


class TestEnviarNotificacion:
    def test_enviar_por_email(self):
        result = asyncio.run(
            notificaciones_service.enviar_notificacion(
                "email", "test@gmail.com", "Asunto", "Cuerpo"
            )
        )
        assert "email" in result

    def test_enviar_por_sms_simulado(self, caplog):
        import logging

        with caplog.at_level(logging.INFO):
            result = asyncio.run(
                notificaciones_service.enviar_notificacion(
                    "sms", "+573009999999", "Asunto", "Mensaje SMS"
                )
            )
        assert "simulado" in result.lower()
        assert any("[SMS simulado]" in r.message for r in caplog.records)
