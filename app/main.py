from fastapi import FastAPI
from dotenv import load_dotenv
import os
from app.config import db
from app.routers import clientes, productos, sucursales, disponibilidad, visitan, transacciones


load_dotenv()


app = FastAPI()


app.include_router(clientes.router)
app.include_router(productos.router)
app.include_router(sucursales.router)
app.include_router(disponibilidad.router)
app.include_router(visitan.router)
app.include_router(transacciones.router)

@app.get("/")
async def root():
    return {"mensaje": "API de Gestión de Fondos de BTG"}

