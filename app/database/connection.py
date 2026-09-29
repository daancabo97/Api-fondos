"""Capa de base de datos — conexión única a MongoDB."""
from pymongo import MongoClient  # pyright: ignore[reportMissingImports]

from app.database.config import DATABASE_NAME, MONGO_URI

client = MongoClient(MONGO_URI)
db = client[DATABASE_NAME]
