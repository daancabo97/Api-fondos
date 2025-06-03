from pydantic import BaseModel, EmailStr
from typing import Optional

class Cliente(BaseModel):
    id: Optional[int] = None
    nombre: str
    apellidos: str
    ciudad: str
    saldo: int = 500000
    email: Optional[EmailStr] = None