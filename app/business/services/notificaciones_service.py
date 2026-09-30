"""Capa de negocio — notificaciones por email o SMS."""
import logging
import os

import httpx
from dotenv import load_dotenv
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema

load_dotenv()

logger = logging.getLogger(__name__)

_mail_conf = ConnectionConfig(
    MAIL_USERNAME=os.getenv("MAIL_USERNAME", "default_user@example.com"),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD", "default_password"),
    MAIL_FROM=os.getenv("MAIL_FROM", "default_from@example.com"),
    MAIL_PORT=int(os.getenv("MAIL_PORT", "587")),
    MAIL_SERVER=os.getenv("MAIL_SERVER", "smtp.gmail.com"),
    MAIL_FROM_NAME="Notificación de Fondos360",
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
)


def _twilio_configurado() -> bool:
    return bool(
        os.getenv("TWILIO_ACCOUNT_SID")
        and os.getenv("TWILIO_AUTH_TOKEN")
        and os.getenv("TWILIO_FROM_NUMBER")
    )


async def _enviar_sms_twilio(destinatario: str, mensaje: str) -> None:
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    from_number = os.getenv("TWILIO_FROM_NUMBER")
    url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post(
            url,
            data={"To": destinatario, "From": from_number, "Body": mensaje},
            auth=(account_sid, auth_token),
        )
        response.raise_for_status()


async def notificar_por_email(evento: dict) -> None:
    """Observador de email. Envía si el evento trae correo."""
    destinatario = str(evento.get("email") or "").strip()
    if not destinatario:
        return
    mensaje_schema = MessageSchema(
        subject=evento["asunto"],
        recipients=[destinatario],
        body=evento["mensaje"],
        subtype="html",
    )
    await FastMail(_mail_conf).send_message(mensaje_schema)
    return "enviado"


async def notificar_por_sms(evento: dict) -> None:
    """Observador de SMS. Envía si el evento trae teléfono."""
    destinatario = str(evento.get("telefono") or "").strip()
    if not destinatario:
        return
    mensaje = evento["mensaje"]
    if _twilio_configurado():
        await _enviar_sms_twilio(destinatario, mensaje)
        return "enviado"
    logger.info("[SMS simulado] -> %s: %s", destinatario, mensaje)
    return "simulado"
