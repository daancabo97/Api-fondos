import re

from pydantic import BaseModel, EmailStr, Field, field_validator


class ClienteRegistro(BaseModel):
    nombre: str
    apellidos: str
    ciudad: str
    saldo: int = 500000
    email: EmailStr
    telefono: str = Field(
        ...,
        min_length=7,
        description="Teléfono de contacto",
        examples=["+573001234567"],
    )

    @field_validator("telefono")
    @classmethod
    def telefono_no_vacio(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("El teléfono es obligatorio")
        return v

    @field_validator("email")
    @classmethod
    def email_must_be_allowed_domain(cls, v: str) -> str:
        allowed_domains = [
            r"@gmail\.com$",
            r"@outlook\.com$",
            r"@hotmail\.com$",
        ]
        if not any(re.search(pattern, v, re.IGNORECASE) for pattern in allowed_domains):
            raise ValueError(
                "El correo debe ser de dominio gmail.com, outlook.com o hotmail.com"
            )
        return v


class ClienteCreateRequest(BaseModel):
    cliente: ClienteRegistro
    password: str

    model_config = {
        "json_schema_extra": {
            "example": {
                "cliente": {
                    "nombre": "Juan",
                    "apellidos": "Pérez",
                    "ciudad": "Bogotá",
                    "saldo": 500000,
                    "email": "juan@gmail.com",
                    "telefono": "+573001234567",
                },
                "password": "Password123*",
            }
        }
    }
