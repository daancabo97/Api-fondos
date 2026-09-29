"""Capa de negocio — notificaciones por email o SMS."""
import logging
import os
from typing import Literal

import httpx
from dotenv import load_dotenv
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema

load_dotenv()

logger = logging.getLogger(__name__)

CanalNotificacion = Literal["email", "sms"]

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


async def _enviar_email(destinatario: str, asunto: str, mensaje: str) -> None:
    mensaje_schema = MessageSchema(
        subject=asunto,
        recipients=[destinatario],
        body=mensaje,
        subtype="html",
    )
    await FastMail(_mail_conf).send_message(mensaje_schema)


def _twilio_configurado() -> bool:
    return bool(
        os.getenv("TWILIO_ACCOUNT_SID")
        and os.getenv("TWILIO_AUTH_TOKEN")
        and os.getenv("TWILIO_FROM_NUMBER")
    )


def _enviar_sms_twilio(destinatario: str, mensaje: str) -> None:
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    from_number = os.getenv("TWILIO_FROM_NUMBER")
    url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"
    response = httpx.post(
        url,
        data={"To": destinatario, "From": from_number, "Body": mensaje},
        auth=(account_sid, auth_token),
        timeout=15.0,
    )
    response.raise_for_status()


def _enviar_sms(destinatario: str, mensaje: str) -> None:
    if _twilio_configurado():
        _enviar_sms_twilio(destinatario, mensaje)
        return
    logger.info("[SMS simulado] -> %s: %s", destinatario, mensaje)


async def enviar_notificacion(
    canal: CanalNotificacion,
    destinatario: str,
    asunto: str,
    mensaje: str,
) -> str:
    if canal == "email":
        await _enviar_email(destinatario, asunto, mensaje)
        return f"Notificación enviada por email a {destinatario}"
    _enviar_sms(destinatario, mensaje)
    if _twilio_configurado():
        return f"Notificación enviada por SMS (Twilio) a {destinatario}"
    return f"Notificación registrada por SMS (simulado) a {destinatario}"


def obtener_canal_contacto_notificacion(
    cliente: dict,
) -> tuple[CanalNotificacion | None, str | None]:
    canal = cliente.get("canal_notificacion", "email")
    if canal == "sms":
        telefono = cliente.get("telefono")
        return ("sms", telefono) if telefono else (None, None)
    email = cliente.get("email")
    return ("email", email) if email else (None, None)
