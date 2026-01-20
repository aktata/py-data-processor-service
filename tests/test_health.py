from __future__ import annotations


async def test_health(client) -> None:
    response = await client.get("/health")
    payload = response.json()
    assert response.status_code == 200
    assert payload["code"] == 0
    assert payload["data"]["status"] == "ok"
    assert "trace_id" in payload
