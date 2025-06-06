from pydantic import BaseModel

class Inscripcion(BaseModel):
    idCliente: str
    idProducto: str
