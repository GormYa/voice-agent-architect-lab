from __future__ import annotations

import asyncio

from .voice_designer import build_voice_persona


async def generate_persona(name: str, era: str, mood: str) -> tuple[str, dict]:
    await asyncio.sleep(0)
    p = build_voice_persona(name, era, mood)
    return name, p.__dict__


async def generate_group(entities: list[tuple[str, str, str]]) -> dict[str, dict]:
    tasks = [generate_persona(*e) for e in entities]
    results = await asyncio.gather(*tasks)
    return {k: v for k, v in results}
