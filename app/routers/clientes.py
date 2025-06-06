from fastapi import APIRouter, HTTPException, status, Depends, Body, Request
from app.database import clientes_collection
from app.schemas.cliente_DTO import Cliente
from app.services.auth import get_password_hash, verify_password, create_access_token, is_strong_password
from bson import ObjectId
from app.services.auth import is_token_revoked

# --- Rate limiting ---
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
router = APIRouter()


def cliente_serializer(cliente) -> dict:
    """Convierte los ObjectId y limpia el campo _id. Elimina el password de la respuesta. El id va primero."""
    data = {}
    data["id"] = str(cliente["_id"])
    # Agregar el resto de los campos en el orden original, excepto _id y password
    for k, v in cliente.items():
        if k not in ("_id", "password"):
            data[k] = v
    return data


@router.get("/clientes/")
async def obtener_clientes():
    clientes = list(clientes_collection.find().sort("_id", 1))  
    clientes_serializados = [cliente_serializer(cliente) for cliente in clientes]
    return clientes_serializados


@router.post("/clientes/")
async def crear_cliente(cliente: Cliente, password: str = Body(...)):
    # Verificar email único
    if clientes_collection.find_one({"email": cliente.email}):
        raise HTTPException(status_code=400, detail="El email ya está registrado")
    # Validar password mínimo 8 caracteres
    if len(password) < 8:
        raise HTTPException(status_code=400, detail="El password debe tener al menos 8 caracteres")
    cliente_dict = cliente.dict()
    cliente_dict["password"] = get_password_hash(password)
    resultado = clientes_collection.insert_one(cliente_dict)
    cliente_dict["_id"] = str(resultado.inserted_id)
    cliente_dict["id"] = str(resultado.inserted_id) 
    return {"id": cliente_dict["id"]}


@router.get("/clientes/{id}")
async def obtener_cliente(id: str):
    cliente = clientes_collection.find_one({"_id": ObjectId(id)})
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return cliente_serializer(cliente)


@router.delete("/clientes{id}")
async def eliminar_cliente(id: str):
    resultado = clientes_collection.delete_one({"_id": ObjectId(id)})
    if resultado.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return {"mensaje": "Cliente eliminado correctamente"}


@router.put("/clientes/{id}")
async def actualizar_saldo(id: str, nuevo_saldo: int):
    resultado = clientes_collection.update_one({"_id": ObjectId(id)}, {"$set": {"saldo": nuevo_saldo}})
    if resultado.modified_count == 0:
        raise HTTPException(status_code=404, detail="Cliente no encontrado o saldo no actualizado")
    return {"mensaje": "Saldo actualizado correctamente"}


@router.post("/login")
@limiter.limit("5/minute")  # 5 intentos por minuto por IP
async def login(request: Request, email: str = Body(...), password: str = Body(...)):
    cliente = clientes_collection.find_one({"email": email})
    if not cliente or not verify_password(password, cliente["password"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales incorrectas")
    token = create_access_token({"sub": str(cliente["_id"]), "rol": cliente.get("rol", "cliente")})
    return {"access_token": token, "token_type": "bearer"}


# Endpoint para revocar token (logout)
from app.database import db
revoked_tokens_collection = db["revoked_tokens"]

@router.post("/logout")
async def logout(request: Request):
    token = request.headers.get('authorization', '').replace('Bearer ', '')
    if not token:
        raise HTTPException(status_code=400, detail="Token no proporcionado")
    revoked_tokens_collection.insert_one({"token": token})
    return {"message": "Token revocado correctamente"}

