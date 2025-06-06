from pydantic import BaseModel
from typing import Optional
from typing import Literal
from datetime import datetime

class Transaccion(BaseModel):
    idCliente: int
    idProducto: int
    fecha: Optional[datetime] = datetime.now()
    tipo: Literal["apertura", "cancelacion"]
    monto: Optional[float]
