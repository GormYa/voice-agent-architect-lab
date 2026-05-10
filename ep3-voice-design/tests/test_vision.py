from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from pipeline.vision import classify_entity


def test_classify_statue():
    e = classify_entity("A marble statue in sunlight")
    assert e.label == "statue"
    assert e.era == "classical"
