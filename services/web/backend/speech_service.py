"""Whole-recording speech adapter. Speaker IDs are scoped to one recording."""
from __future__ import annotations

import httpx
from .audio_processor import format_timestamp
from .ml_service import MLServiceError


def map_timeline(result: dict) -> list[dict]:
    timeline = result.get("timeline")
    if not isinstance(timeline, list) or not timeline:
        raise MLServiceError("Speech response has no timeline", "Сервис речи вернул пустой транскрипт.")
    lines = []
    for item in timeline:
        start_ms = round(float(item["start"]) * 1000)
        end_ms = round(float(item["end"]) * 1000)
        if start_ms < 0 or end_ms < start_ms:
            raise ValueError("Invalid speech timestamps")
        lines.append({
            "chunk_id": 1, "start_ms": start_ms, "end_ms": end_ms,
            "start_time": format_timestamp(start_ms / 1000),
            "speaker": item.get("display_name") or item.get("source_speaker", "unknown"),
            "speaker_id": item.get("speaker_id"),
            "source_speaker": item.get("source_speaker", "unknown"),
            "role": item.get("role", "unknown"), "text": item.get("text", ""),
            "is_final": True,
        })
    return sorted(lines, key=lambda line: line["start_ms"])


class SpeechServiceClient:
    def __init__(self, base_url: str, *, client: httpx.AsyncClient | None = None):
        self.base_url = base_url.rstrip("/")
        self.client = client

    async def transcribe(self, file_bytes: bytes, file_name: str, content_type: str | None) -> dict:
        async def request(client):
            response = await client.post(
                self.base_url + "/transcribe",
                files={"file": (file_name, file_bytes, content_type or "application/octet-stream")},
                timeout=7200,
            )
            response.raise_for_status()
            result = response.json()
            map_timeline(result)
            return result
        try:
            if self.client is not None:
                return await request(self.client)
            async with httpx.AsyncClient() as client:
                return await request(client)
        except (httpx.HTTPError, ValueError, KeyError, TypeError) as exc:
            raise MLServiceError(str(exc), "Не удалось обработать запись в локальном сервисе речи.") from exc
