from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from stream.chunk_scheduler import ChunkScheduler, split_for_stream


def test_split_for_stream():
    scheduler = ChunkScheduler(schedule=[5, 5])
    out = split_for_stream("abcdefghijk", scheduler)
    assert out == ["abcde", "fghij", "k"]
