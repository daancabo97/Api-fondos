"""Capa de base de datos — configuración y variables de entorno."""
import os

from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "BTG")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development").lower()
# Default solo para desarrollo local — en producción definir SECRET_KEY en .env
SECRET_KEY = os.getenv("SECRET_KEY", "firma_token")
_DEFAULT_SECRET = "firma_token"


def validate_production_config() -> None:
    """En producción exige SECRET_KEY distinta al default de desarrollo."""
    if ENVIRONMENT != "production":
        return
    if not SECRET_KEY or SECRET_KEY == _DEFAULT_SECRET:
        raise RuntimeError(
            "ENVIRONMENT=production requiere SECRET_KEY propia en .env "
            "(openssl rand -hex 32)"
        )
