from pydantic import BaseModel

class Visita(BaseModel):
    idSucursal: str
    idCliente: str
    fechaVisita: str
