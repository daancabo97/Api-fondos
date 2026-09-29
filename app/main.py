"""
Patrón: Composition Root — ensambla la aplicación FastAPI.
Arquitectura: presentation -> business -> persistence -> database
"""
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.database.config import validate_production_config
from app.database.connection import client as mongo_client
from app.persistence import (
    cliente_repository,
    inscripcion_repository,
    sequence_repository,
    visita_repository,
)
from app.presentation.limiter import limiter
from app.presentation.routers import (
    clientes,
    disponibilidad,
    productos,
    sucursales,
    transacciones,
    visitas,
)

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    validate_production_config()
    visita_repository.ensure_collection()
    cliente_repository.ensure_indexes()
    inscripcion_repository.ensure_indexes()
    sequence_repository.sync_client_sequence()
    yield


app = FastAPI(
    title="Fondos360",
    description="API de gestión de fondos de inversión",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)


app.include_router(clientes.router)
app.include_router(productos.router)
app.include_router(sucursales.router)
app.include_router(disponibilidad.router)
app.include_router(visitas.router)
app.include_router(transacciones.router)


@app.get("/")
async def root():
    return {"mensaje": "API de Gestión de Fondos 360"}


@app.get("/health")
async def health():
    try:
        mongo_client.admin.command("ping")
        return {"status": "ok", "mongodb": "connected"}
    except Exception:
        return JSONResponse(
            status_code=503,
            content={"status": "error", "mongodb": "disconnected"},
        )
