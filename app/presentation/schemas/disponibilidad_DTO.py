from pydantic import BaseModel

class Disponibilidad(BaseModel):
    idSucursal: int
    nombre: str
    idProducto: int
