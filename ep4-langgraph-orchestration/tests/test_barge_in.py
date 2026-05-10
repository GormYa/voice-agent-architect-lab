from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from graph.barge_in import detect_barge_in


def test_barge_in_threshold():
    assert detect_barge_in(0.7)
    assert not detect_barge_in(0.5)
