from __future__ import annotations


async def test_process_image_upload(client, sample_image_bytes) -> None:
    files = {"file": ("sample.png", sample_image_bytes, "image/png")}
    response = await client.post("/process", files=files)
    body = response.json()
    assert response.status_code == 200
    assert body["code"] == 0
    assert body["data"]["input_type"] == "image"
    assert body["data"]["source"] == "file_upload"
    assert set(body["data"]["timings_ms"]) == {"parse", "validate", "process", "total"}
    assert set(body["data"]["limits"]) == {"max_bytes", "json_max_depth", "json_max_nodes"}
    assert body["data"]["summary"]["format"] == "PNG"
