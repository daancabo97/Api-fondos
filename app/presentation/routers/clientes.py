"""Capa de presentación - endpoints de clientes."""
from fastapi import APIRouter, Body, Depends, Request

from app.business import cliente_service
from app.presentation.dependencies.auth_deps import (
    get_current_user,
    require_admin,
    require_authenticated,
)
from app.presentation.limiter import limiter
from app.presentation.schemas.cliente_DTO import ClienteCreateRequest

router = APIRouter()


@router.get("/clientes/")
async def obtener_clientes(_user=Depends(require_admin)):
    return cliente_service.listar_clientes()


@router.post("/clientes/", response_model=None)
async def crear_cliente(request: ClienteCreateRequest):
    return cliente_service.registrar_cliente(
        request.cliente.model_dump(), request.password
    )


@router.get("/clientes/{id}")
async def obtener_cliente(id: str, user=Depends(require_authenticated)):
    return cliente_service.obtener_cliente(id, user)


@router.delete("/clientes/{id}")
async def eliminar_cliente(id: str, user=Depends(require_authenticated)):
    return cliente_service.eliminar_cliente(id, user)


@router.put("/clientes/{id}")
async def actualizar_saldo(id: str, nuevo_saldo: int, _user=Depends(require_admin)):
    return cliente_service.actualizar_saldo(id, nuevo_saldo)


@router.post("/login")
@limiter.limit("5/minute")
async def login(request: Request, email: str = Body(...), password: str = Body(...)):
    return cliente_service.login(email, password)


@router.post("/logout")
async def logout(user=Depends(get_current_user)):
    return cliente_service.logout(user["token"])
