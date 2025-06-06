from pydantic import BaseModel, EmailStr, validator
from typing import Optional
import re

class Cliente(BaseModel):
    id: Optional[int] = None
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
