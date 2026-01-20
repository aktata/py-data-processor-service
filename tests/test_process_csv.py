from __future__ import annotations


async def test_process_csv_upload(client, data_dir) -> None:
    csv_path = data_dir / "sample.csv"
    files = {"file": ("sample.csv", csv_path.read_bytes(), "text/csv")}
    response = await client.post("/process", files=files)
    body = response.json()
    assert response.status_code == 200
    assert body["code"] == 0
    assert body["data"]["input_type"] == "csv"
    assert body["data"]["source"] == "file_upload"
    assert "warnings" in body["data"]
    assert set(body["data"]["timings_ms"]) == {"parse", "validate", "process", "total"}
    assert set(body["data"]["limits"]) == {"max_bytes", "json_max_depth", "json_max_nodes"}
    assert body["data"]["summary"]["rows"] == 4
