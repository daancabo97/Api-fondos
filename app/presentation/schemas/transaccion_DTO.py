from pydantic import BaseModel

class Transaccion(BaseModel):
    idCliente: int
    idProducto: int
