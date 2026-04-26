from __future__ import annotations

from collections.abc import AsyncIterator, Iterator

import pytest
from fastapi.testclient import TestClient

from app.db.session import get_db_session
from app.main import app


@pytest.fixture
def client() -> Iterator[TestClient]:
    async def override_get_db_session() -> AsyncIterator[object]:
        yield object()

    app.dependency_overrides[get_db_session] = override_get_db_session

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
