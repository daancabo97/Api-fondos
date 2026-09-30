from fastapi_mail import FastMail

mensajes_email: list[dict] = []


def aplicar_mock() -> None:
    """Sustituye el envío real y guarda asunto, destinatario y cuerpo."""

    async def fake_send_message(self, message_schema):
        mensajes_email.append(
            {
                "subject": message_schema.subject,
                "recipients": list(message_schema.recipients),
                "body": message_schema.body,
            }
        )

    FastMail.send_message = fake_send_message


def limpiar_mensajes_email() -> None:
    mensajes_email.clear()
