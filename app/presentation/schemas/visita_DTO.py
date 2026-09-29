from pydantic import BaseModel

class Visita(BaseModel):
    idSucursal: int
    idCliente: int
    fechaVisita: str
