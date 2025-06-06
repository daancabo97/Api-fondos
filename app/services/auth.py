from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from passlib.context import CryptContext
import re
from app.database import clientes_collection
from app.database import db  # Para acceder a la base de datos

SECRET_KEY = "tu_clave_secreta"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Colección para tokens revocados
revoked_tokens_collection = db["revoked_tokens"]

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def is_strong_password(password: str) -> bool:
    # Al menos 8 caracteres, una mayúscula, una minúscula, un número y un símbolo
    return (
        len(password) >= 8 and
        re.search(r"[A-Z]", password) and
        re.search(r"[a-z]", password) and
        re.search(r"[0-9]", password) and
        re.search(r"[^A-Za-z0-9]", password)
    )


def get_password_hash(password):
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta=None):
    from datetime import datetime, timedelta
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def is_token_revoked(token: str) -> bool:
    return revoked_tokens_collection.find_one({"token": token}) is not None

def get_current_user(token: str = Depends(oauth2_scheme)):
    # Verificar si el token está revocado
    if is_token_revoked(token):
        raise HTTPException(status_code=401, detail="Token revocado")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        rol = payload.get("rol")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Token inválido")
        return {"user_id": user_id, "rol": rol}
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido")
