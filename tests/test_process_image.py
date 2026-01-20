from __future__ import annotations


async def test_process_image_upload(client, sample_image_bytes) -> None:
    files = {"file": ("sample.png", sample_image_bytes, "image/png")}
    response = await client.post("/process", files=files)
    body = response.json()
    assert response.status_code == 200
    assert body["code"] == 0
    assert body["data"]["input_type"] == "image"
    assert body["data"]["summary"]["format"] == "PNG"
