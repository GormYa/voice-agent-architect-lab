from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from graph.speculative import (
    SENTENCE_BOUNDARY_RE,
    collect_speculative_chunks,
    simulate_speculative_stream,
    stream_tokens_with_boundaries,
)


def test_sentence_boundary_regex_matches_terminal_punctuation():
    assert SENTENCE_BOUNDARY_RE.search("First sentence.")
    assert SENTENCE_BOUNDARY_RE.search("Question?")
    assert SENTENCE_BOUNDARY_RE.search("Excited!")
    assert not SENTENCE_BOUNDARY_RE.search("No boundary yet")


def test_collect_speculative_chunks_emits_on_sentence_boundaries():
    tokens = "First sentence. Second sentence! Final thought?".split()
    chunks = collect_speculative_chunks(tokens)

    assert chunks == [
        "First sentence.",
        "Second sentence!",
        "Final thought?",
    ]


def test_simulate_speculative_stream_records_tts_send_timestamps():
    tokens = "One. Two. Three.".split()
    events = simulate_speculative_stream(tokens, token_interval_ms=40, send_overhead_ms=20)

    assert len(events) == 3
    assert events[0].text == "One."
    assert events[0].sent_at_ms > 0
    assert events[0].tts_id == "tts-1"
    assert events[1].sent_at_ms > events[0].sent_at_ms


def test_stream_tokens_with_boundaries_dispatches_per_sentence():
    sent = []

    def send_tts(chunk: str) -> str:
        sent.append(chunk)
        return f"id-{len(sent)}"

    ids = stream_tokens_with_boundaries(
        tokens="Alpha. Beta sentence! Last line?".split(),
        send_tts=send_tts,
    )

    assert sent == ["Alpha.", "Beta sentence!", "Last line?"]
    assert ids == ["id-1", "id-2", "id-3"]
