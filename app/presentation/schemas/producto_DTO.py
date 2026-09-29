from typing import Optional

from pydantic import BaseModel

class Producto(BaseModel):
    id: Optional[int]
    nombre: str
    monto_minimo: int
    categoria: str
