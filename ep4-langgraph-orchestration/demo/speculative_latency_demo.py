from __future__ import annotations

from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from graph.speculative import simulate_speculative_stream


def full_response_latency_ms(
    tokens: list[str],
    *,
    token_interval_ms: int,
    send_overhead_ms: int,
) -> int:
    return len(tokens) * token_interval_ms + send_overhead_ms


def main() -> None:
    text = (
        "This Roman statue once watched over river trade in the city. "
        "Notice the powerful posture and carved drapery. "
        "The expression suggests protection and authority."
    )
    tokens = text.split()
    token_interval_ms = 40
    send_overhead_ms = 25

    speculative_events = simulate_speculative_stream(
        tokens,
        token_interval_ms=token_interval_ms,
        send_overhead_ms=send_overhead_ms,
    )
    full_ms = full_response_latency_ms(
        tokens,
        token_interval_ms=token_interval_ms,
        send_overhead_ms=send_overhead_ms,
    )
    first_spec_ms = speculative_events[0].sent_at_ms if speculative_events else full_ms
    delta_ms = full_ms - first_spec_ms

    print("=== Speculative TTS Latency Demo ===")
    print(f"Total tokens: {len(tokens)}")
    print(f"Token interval: {token_interval_ms} ms")
    print(f"TTS dispatch overhead: {send_overhead_ms} ms")
    print()
    print(f"Full-response first audio start: {full_ms} ms")
    print(f"Speculative first audio start: {first_spec_ms} ms")
    print(f"Latency improvement: {delta_ms} ms")
    print()
    print("Speculative dispatch timeline:")
    for event in speculative_events:
        print(f"- {event.sent_at_ms:>4} ms | {event.tts_id:<6} | {event.text}")


if __name__ == "__main__":
    main()
