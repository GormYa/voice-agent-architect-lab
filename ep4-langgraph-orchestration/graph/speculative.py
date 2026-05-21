from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Callable


SENTENCE_BOUNDARY_RE = re.compile(r"[.!?][\"')\]]?$")


@dataclass
class TTSDispatchEvent:
    text: str
    sent_at_ms: int
    tts_id: str


def speculative_response(prefix: str, likely_intent: str) -> str:
    return f"{prefix} (speculative): {likely_intent}"


def collect_speculative_chunks(tokens: list[str]) -> list[str]:
    chunks: list[str] = []
    buffer: list[str] = []
    for token in tokens:
        buffer.append(token)
        candidate = " ".join(buffer).strip()
        if SENTENCE_BOUNDARY_RE.search(token):
            chunks.append(candidate)
            buffer = []
    if buffer:
        chunks.append(" ".join(buffer).strip())
    return chunks


def stream_tokens_with_boundaries(
    *,
    tokens: list[str],
    send_tts: Callable[[str], str],
) -> list[str]:
    in_flight_tts: list[str] = []
    token_buffer: list[str] = []
    for token in tokens:
        token_buffer.append(token)
        if SENTENCE_BOUNDARY_RE.search(token):
            chunk = " ".join(token_buffer).strip()
            tts_id = send_tts(chunk)
            in_flight_tts.append(tts_id)
            token_buffer = []
    if token_buffer:
        chunk = " ".join(token_buffer).strip()
        tts_id = send_tts(chunk)
        in_flight_tts.append(tts_id)
    return in_flight_tts


def simulate_speculative_stream(
    tokens: list[str],
    *,
    token_interval_ms: int = 35,
    send_overhead_ms: int = 12,
) -> list[TTSDispatchEvent]:
    events: list[TTSDispatchEvent] = []
    elapsed_ms = 0
    tts_counter = 0
    token_buffer: list[str] = []

    for token in tokens:
        elapsed_ms += token_interval_ms
        token_buffer.append(token)
        if SENTENCE_BOUNDARY_RE.search(token):
            elapsed_ms += send_overhead_ms
            tts_counter += 1
            events.append(
                TTSDispatchEvent(
                    text=" ".join(token_buffer).strip(),
                    sent_at_ms=elapsed_ms,
                    tts_id=f"tts-{tts_counter}",
                )
            )
            token_buffer = []
    if token_buffer:
        elapsed_ms += send_overhead_ms
        tts_counter += 1
        events.append(
            TTSDispatchEvent(
                text=" ".join(token_buffer).strip(),
                sent_at_ms=elapsed_ms,
                tts_id=f"tts-{tts_counter}",
            )
        )
    return events
