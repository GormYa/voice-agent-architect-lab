from __future__ import annotations

import asyncio
import json
import logging
import time

from dotenv import load_dotenv
from fastapi import FastAPI, Request


load_dotenv()

from ghl_webhook import create_ghl_contact
from lead_store import upsert_lead
from retell_auth import verify_retell_signature


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ep6.retell")
app = FastAPI(title="EP6 Retell Custom Backend")


@app.post("/retell-webhook")
async def retell_webhook(request: Request):
    start = time.perf_counter()
    body = await verify_retell_signature(request)
    data = json.loads(body)
    variables = data["variables"]
    name = data["variables"].get("caller_name", "there")
    appt = data["variables"].get("appointment_time", "soon")
    trigger = data.get("function_name", data.get("event", "qualification"))
    is_qualification = trigger == "qualification"
    upsert_lead(data["call_id"], data["variables"], qualified=is_qualification)
    elapsed_ms = (time.perf_counter() - start) * 1000
    logger.info(f"webhook handled in {elapsed_ms:.0f}ms")
    if is_qualification:
        # fire and forget — does not block Retell response
        asyncio.create_task(create_ghl_contact(variables))
        return {"response": "Connecting you now. One moment."}
    return {"response": f"Perfect, {name}. Your appointment is confirmed for {appt}."}
