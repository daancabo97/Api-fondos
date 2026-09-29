from fastapi_mail import FastMail


def aplicar_mock() -> None:
    async def fake_send_message(self, message_schema):
        return None

    FastMail.send_message = fake_send_message
