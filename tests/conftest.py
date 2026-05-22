import pytest

from flagme.api import _store


@pytest.fixture(autouse=True)
def _reset_store() -> None:
    _store.clear()
