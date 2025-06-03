from pydantic import BaseModel
from typing import Optional

class Sucursal(BaseModel):
    id: Optional[int] = None
    nombre: str
    ciudad: str
