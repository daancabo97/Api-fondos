"""Capa de persistencia - tokens JWT revocados."""
from app.database.connection import db

_collection = db["revoked_tokens"]


def is_revoked(token: str) -> bool:
    return _collection.find_one({"token": token}) is not None


def revoke(token: str) -> None:
    _collection.insert_one({"token": token})
