from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import PlainTextResponse

from bridge.media_stream import process_twilio_media_event

app = FastAPI(title="EP2 Twilio AEC Demo")
LOG_PATH = Path("ep2-telephony-bridge/logs/call_transcripts.jsonl")


def _log(record: dict) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")


@app.get("/health")
def health() -> dict:
    return {"ok": True, "aec_enabled": os.getenv("AEC_ENABLED", "1") == "1"}


@app.post("/twilio/voice", response_class=PlainTextResponse)
async def twilio_voice(request: Request) -> str:
    # Set PUBLIC_WS_URL to your ngrok/wss endpoint, e.g. wss://abc.ngrok-free.app/twilio/media
    ws_url = os.getenv("PUBLIC_WS_URL", "wss://example.ngrok-free.app/twilio/media")
    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Say>Connecting you to the voice demo bridge.</Say>
  <Connect>
    <Stream url="{ws_url}" />
  </Connect>
</Response>"""
    return twiml


@app.websocket("/twilio/media")
async def twilio_media(ws: WebSocket) -> None:
    await ws.accept()
    last_speaker_frame = b""
    stream_sid = "unknown"

    try:
        while True:
            raw = await ws.receive_text()
            payload = json.loads(raw)
            event_type = payload.get("event")

            if event_type == "start":
                stream_sid = payload.get("start", {}).get("streamSid", "unknown")
                _log({
                    "ts_utc": datetime.now(timezone.utc).isoformat(),
                    "stream_sid": stream_sid,
                    "event": "start",
                    "aec_enabled": os.getenv("AEC_ENABLED", "1") == "1",
                })
                continue

            if event_type == "media":
                # For a stricter demo, use outbound speaker audio as last_speaker_frame reference.
                processed_json = process_twilio_media_event(raw, last_speaker_frame=last_speaker_frame)
                processed = json.loads(processed_json)
                dbg = processed.get("debug", {})

                _log({
                    "ts_utc": datetime.now(timezone.utc).isoformat(),
                    "stream_sid": stream_sid,
                    "event": "media",
                    "aec_enabled": dbg.get("aec_enabled"),
                    "suppressed": dbg.get("suppressed"),
                    "correlation": dbg.get("correlation"),
                    "stt_text": dbg.get("stt_text"),
                })

                # Keep a simple rolling reference for demo purposes.
                last_speaker_frame = b"\x11\x22" * 160
                continue

            if event_type == "stop":
                _log({
                    "ts_utc": datetime.now(timezone.utc).isoformat(),
                    "stream_sid": stream_sid,
                    "event": "stop",
                })
                break

    except WebSocketDisconnect:
        _log({
            "ts_utc": datetime.now(timezone.utc).isoformat(),
            "stream_sid": stream_sid,
            "event": "disconnect",
        })


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("demo_twilio_server:app", host="0.0.0.0", port=8022, reload=False)
