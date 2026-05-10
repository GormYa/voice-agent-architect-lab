from __future__ import annotations

import json

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse

from stream.cascade import stream_cascade

app = FastAPI(title="EP1 Realtime TTS")


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
                await ws.send_json(event)
    except WebSocketDisconnect:
        return
