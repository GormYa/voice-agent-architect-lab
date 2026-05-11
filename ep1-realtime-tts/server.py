from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse

from stream.cascade import stream_cascade

app = FastAPI(title="EP1 Realtime TTS")
LOG_PATH = Path("ep1-realtime-tts/logs/latency.jsonl")


@app.get("/")
def home() -> FileResponse:
    return FileResponse("ep1-realtime-tts/static/index.html")


@app.websocket("/ws")
async def ws_stream(ws: WebSocket) -> None:
    await ws.accept()
    try:
        while True:
            payload = await ws.receive_text()
            data = json.loads(payload)
            text = str(data.get("text", "")).strip()
            if not text:
                await ws.send_json({"type": "error", "message": "text is required"})
                continue
            async for event in stream_cascade(text):
                if event.get("type") == "done":
                    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
                    log_event = {
                        "ts_utc": datetime.now(timezone.utc).isoformat(),
                        "input_text": text,
                        "timestamps_ms": event.get("timestamps_ms", {}),
                        "breakdown_ms": event.get("breakdown_ms", {}),
                        "total_latency_ms": event.get("total_latency_ms"),
                    }
                    with LOG_PATH.open("a", encoding="utf-8") as f:
                        f.write(json.dumps(log_event) + "\n")
                await ws.send_json(event)
    except WebSocketDisconnect:
        return
