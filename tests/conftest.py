from __future__ import annotations

import base64
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture(scope="session")
def data_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "data"


@pytest.fixture(scope="session")
def sample_image_bytes(data_dir: Path) -> bytes:
    encoded = (data_dir / "sample_image_base64.txt").read_text().strip()
    return base64.b64decode(encoded)


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture
async def client() -> AsyncClient:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
