"""Tests — app.persistence.visita_repository (migración visitan → visitas)."""
from datetime import datetime

from app.database.connection import db
from app.persistence import visita_repository


def _reset_visitas_collections() -> None:
    for name in ("visitan", "visitas"):
        if name in db.list_collection_names():
            db[name].drop()


class TestEnsureCollection:
    def test_renombra_solo_visitan(self):
        _reset_visitas_collections()
        db["visitan"].insert_one(
            {"idSucursal": 1, "idCliente": 1, "fechaVisita": datetime(2024, 1, 1)}
        )

        visita_repository.ensure_collection()

        assert "visitan" not in db.list_collection_names()
        assert db["visitas"].count_documents({}) == 1

    def test_fusiona_ambas_sin_duplicar(self):
        _reset_visitas_collections()
        fecha = datetime(2024, 2, 1)
        db["visitas"].insert_one(
            {"idSucursal": 10, "idCliente": 20, "fechaVisita": fecha}
        )
        db["visitan"].insert_many(
            [
                {"idSucursal": 10, "idCliente": 20, "fechaVisita": fecha},
                {"idSucursal": 11, "idCliente": 21, "fechaVisita": datetime(2024, 3, 1)},
            ]
        )

        visita_repository.ensure_collection()

        assert "visitan" not in db.list_collection_names()
        assert db["visitas"].count_documents({}) == 2
        sucursales = sorted(v["idSucursal"] for v in db["visitas"].find())
        assert sucursales == [10, 11]

    def test_sin_visitan_no_hace_nada(self):
        _reset_visitas_collections()
        db["visitas"].insert_one(
            {"idSucursal": 99, "idCliente": 88, "fechaVisita": datetime(2024, 4, 1)}
        )

        visita_repository.ensure_collection()

        assert "visitan" not in db.list_collection_names()
        assert db["visitas"].count_documents({}) == 1
