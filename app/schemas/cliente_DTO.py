from pydantic import BaseModel, EmailStr, validator
from typing import Optional
import re

class Cliente(BaseModel):
    id: Optional[int] = None  # Cambiado a opcional
    nombre: str
    apellidos: str
    ciudad: str
    saldo: int = 500000
    email: EmailStr  # Ahora obligatorio
    rol: str = "cliente"

    @validator('email')
    def email_must_be_allowed_domain(cls, v):
        allowed_domains = [
            r'@gmail\.com$',
            r'@outlook\.com$',
            r'@hotmail\.com$'
        ]
        if not any(re.search(pattern, v, re.IGNORECASE) for pattern in allowed_domains):
            raise ValueError('El correo debe ser de dominio gmail.com, outlook.com o hotmail.com')
        return v

class ClienteCreateRequest(BaseModel):
    cliente: Cliente
    password: str
    class Config:
        json_schema_extra = {
            "example": {
                "cliente": {
                    # "id": 1,  # El id NO debe aparecer en el ejemplo
                    "nombre": "pepe",
                    "apellidos": "pepe",
                    "ciudad": "Bogota",
                    "saldo": 50000,
                    "email": "pepe@gmail.com",
                    "rol": "cliente"
                },
                "password": "pepe0000"
            }
        }
