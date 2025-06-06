from fastapi import FastAPI
from dotenv import load_dotenv
from fastapi.openapi.models import OAuthFlows as OAuthFlowsModel
from fastapi.security import OAuth2PasswordBearer
from app.config import db
from app.routers import clientes, productos, sucursales, disponibilidad, visitan, transacciones
import os


load_dotenv()


app = FastAPI()


app.include_router(clientes.router)
app.include_router(productos.router)
app.include_router(sucursales.router)
app.include_router(disponibilidad.router)
app.include_router(visitan.router)
app.include_router(transacciones.router)

app.openapi_schema = None  # Forzar regeneración si ya existe

@app.on_event("startup")
def customize_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = app.openapi()
    openapi_schema["components"]["securitySchemes"] = {
        "OAuth2PasswordBearer": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT"
        }
    }
    for path in openapi_schema["paths"].values():
        for op in path.values():
            op["security"] = [{"OAuth2PasswordBearer": []}]
    app.openapi_schema = openapi_schema
    app.openapi = lambda: app.openapi_schema

customize_openapi()

@app.get("/")
async def root():
    return {"mensaje": "API de Gestión de Fondos 360"}

