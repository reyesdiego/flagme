from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from flagme.api import app, get_storage
from flagme.storage import FlagStorage


@pytest.fixture
def storage() -> Iterator[FlagStorage]:
    s = FlagStorage(":memory:")
    try:
        yield s
    finally:
        s.close()


@pytest.fixture
def client(storage: FlagStorage) -> Iterator[TestClient]:
    app.dependency_overrides[get_storage] = lambda: storage
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()
