import json

from app.vision.models.vision_schema import VisionConstruction


def parse_vision_response(raw: str) -> VisionConstruction:
    data = json.loads(raw)

    return VisionConstruction(**data)