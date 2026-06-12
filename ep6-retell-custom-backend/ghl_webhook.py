from __future__ import annotations

import os

import httpx


GHL_API_KEY = os.environ["GHL_API_KEY"]
GHL_LOCATION_ID = os.environ["GHL_LOCATION_ID"]
GHL_CONTACTS_URL = "https://services.leadconnectorhq.com/contacts/"


async def create_ghl_contact(variables: dict):
    # GHL requires this Version header; without it, requests can fail silently.
    headers = {
        "Authorization": f"Bearer {GHL_API_KEY}",
        "Version": "2021-07-28",
        "Content-Type": "application/json",
    }
    payload = {
        "locationId": GHL_LOCATION_ID,
        "firstName": variables.get("caller_name", ""),
        "phone": variables.get("phone_number", ""),
        "customFields": [
            {"key": "budget", "field_value": variables.get("budget", "")},
            {"key": "timeline", "field_value": variables.get("timeline", "")},
            {"key": "location", "field_value": variables.get("location", "")},
        ],
        "tags": ["voice-ai", "qualified-lead"],
    }

    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(GHL_CONTACTS_URL, headers=headers, json=payload)
        resp.raise_for_status()
        return resp.json()
