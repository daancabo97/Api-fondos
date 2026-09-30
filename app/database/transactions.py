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
    Mete saldo, inscripción y transacción en una sesión de Mongo
    cuando el cluster lo permite. Si no hay sesión,
    _rollback_if_no_mongo_session deshace a mano lo ya escrito.
    """
    if not mongo_supports_transactions():
        return callback(None)
    with client.start_session() as session:
        return session.with_transaction(lambda s: callback(s))
