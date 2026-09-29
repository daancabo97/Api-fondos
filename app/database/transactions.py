"""Utilidades para transacciones MongoDB multi-documento."""
from collections.abc import Callable
from typing import Any, TypeVar

from app.database.connection import client

T = TypeVar("T")


def mongo_supports_transactions() -> bool:
    """True si el cluster es replica set o mongos (admite with_transaction)."""
    try:
        hello = client.admin.command("hello")
        return bool(hello.get("setName") or hello.get("msg") == "isdbgrid")
    except Exception:
        return False


def run_in_transaction(callback: Callable[[Any], T]) -> T:
    """
    Ejecuta callback(session) dentro de with_transaction si el cluster lo permite.
    En standalone dev, callback recibe session=None y el caller usa rollback manual.
    """
    if not mongo_supports_transactions():
        return callback(None)
    with client.start_session() as session:
        return session.with_transaction(lambda s: callback(s))
