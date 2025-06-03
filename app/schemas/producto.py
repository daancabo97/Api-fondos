from pydantic import BaseModel
from typing import Optional

class Producto(BaseModel):
    id: Optional[int]
    nombre: str
    monto_minimo: int
    categoria: str
