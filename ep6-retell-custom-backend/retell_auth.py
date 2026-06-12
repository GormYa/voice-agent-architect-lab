from __future__ import annotations

import hashlib
import hmac
import os

from fastapi import HTTPException, Request


RETELL_SECRET = os.environ["RETELL_WEBHOOK_SECRET"]


async def verify_retell_signature(request: Request) -> bytes:
    signature = request.headers.get("x-retell-signature", "")
    body = await request.body()

    expected = hmac.new(
        key=RETELL_SECRET.encode("utf-8"),
        msg=body,
        digestmod=hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(signature, expected):  # constant-time — prevents timing attacks
        raise HTTPException(status_code=401)

    return body
