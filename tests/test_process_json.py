from __future__ import annotations


async def test_process_json_payload(client) -> None:
    payload = {"hello": "world", "items": [1, 2, 3]}
    response = await client.post("/process", json=payload)
    body = response.json()
    assert response.status_code == 200
    assert body["code"] == 0
    assert body["data"]["input_type"] == "json"
    assert "summary" in body["data"]
