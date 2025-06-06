from pydantic import BaseModel

class Disponibilidad(BaseModel):
    idSucursal: str
    idProducto: str
