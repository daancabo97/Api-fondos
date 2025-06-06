from pydantic import BaseModel, EmailStr
from typing import Optional

class Cliente(BaseModel):
    nombre: str
    apellidos: str
    ciudad: str
    saldo: int = 500000
    email: EmailStr  # Ahora obligatorio
    rol: str = "cliente"
