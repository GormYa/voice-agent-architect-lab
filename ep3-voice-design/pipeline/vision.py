from __future__ import annotations

from dataclasses import dataclass


@dataclass
class VisionEntity:
    label: str
    era: str
    mood: str


def classify_entity(image_caption: str) -> VisionEntity:
    text = image_caption.lower()
    if "statue" in text or "marble" in text:
        return VisionEntity(label="statue", era="classical", mood="calm")
    if "knight" in text:
        return VisionEntity(label="knight", era="medieval", mood="bold")
    return VisionEntity(label="guide", era="modern", mood="friendly")
