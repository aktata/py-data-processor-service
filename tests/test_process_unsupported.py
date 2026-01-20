from __future__ import annotations


async def test_process_unsupported_upload(client) -> None:
    files = {"file": ("sample.txt", b"hello", "text/plain")}
    response = await client.post("/process", files=files)
    body = response.json()
    assert response.status_code == 415
    assert body["code"] == 1002
