"""Verify a running demo through real HTTP without cloud calls or models."""
import io
import os
import time
import wave
import httpx

url = os.getenv("LECTERN_URL", "http://127.0.0.1:8090")
with httpx.Client(base_url=url, timeout=30) as client:
    deadline = time.monotonic() + 60
    while True:
        try:
            config = client.get("/api/config")
            config.raise_for_status()
            break
        except (httpx.HTTPError, ValueError):
            if time.monotonic() >= deadline:
                raise
            time.sleep(1)
    assert config.json()["transcription_backend"] == "demo", "Smoke requires demo mode"
    assert client.get("/").status_code == 200
    data = io.BytesIO()
    with wave.open(data, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(16000)
        wav.writeframes(b"\0\0" * 16000)
    uploaded = client.post("/api/generations/upload", files={"file": ("demo.wav", data.getvalue(), "audio/wav")})
    uploaded.raise_for_status()
    job_id = uploaded.json()["id"]
    deadline = time.monotonic() + 30
    while True:
        response = client.get(f"/api/generations/{job_id}")
        response.raise_for_status()
        result = response.json()
        if result["status"] in ("completed", "failed"):
            break
        assert time.monotonic() < deadline, result
        time.sleep(.2)
    assert result["status"] == "completed", result.get("error_message")
    assert result["transcript"], result
    assert result["analytics"]["local_speech"], result
    assert all("end_ms" in item and "role" in item for item in result["transcript"])
    deleted = client.delete(f"/api/generations/{job_id}")
    deleted.raise_for_status()
    assert client.get(f"/api/generations/{job_id}").status_code == 404
    print("PASS: demo page → upload → completed → transcript/analytics → delete → 404")
