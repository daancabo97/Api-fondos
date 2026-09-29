from typing import Optional

from pydantic import BaseModel

class Sucursal(BaseModel):
    id: Optional[int] = None
    nombre: str
    ciudad: str
