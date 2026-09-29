"""Tests — app.persistence.inscripcion_repository."""
from unittest.mock import patch

from pymongo.errors import OperationFailure

from app.persistence import inscripcion_repository


class TestEnsureIndexes:
    def test_operation_failure_no_propaga(self):
        with patch.object(
            inscripcion_repository._collection,
            "create_index",
            side_effect=OperationFailure("idx exists"),
        ):
            inscripcion_repository.ensure_indexes()
