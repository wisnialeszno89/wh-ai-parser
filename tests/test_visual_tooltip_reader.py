"""Visual tooltip segmentation tests: no live GUI, no OCR binary needed."""
from PIL import Image, ImageDraw

from app.agent.perception.visual_tooltip_reader import (
    changed_regions,
    tooltip_ocr,
)


def test_detects_tooltip_box_near_hover():
    before = Image.new("RGB", (500, 300), "white")
    after = before.copy()
    draw = ImageDraw.Draw(after)
    draw.rectangle((95, 80, 315, 125), fill="#f5e9b3", outline="black", width=2)
    draw.text((105, 94), "Wybierz okucie", fill="black")
    regions = changed_regions(before, after, (76, 76))
    assert regions
    assert any(x1 <= 110 and y1 <= 100 and x2 >= 300
               for x1, y1, x2, y2 in regions)


def test_no_change_no_ocr_candidate():
    image = Image.new("RGB", (200, 120), "white")
    result = tooltip_ocr(image, image, (25, 25))
    assert result["status"] == "no_visual_change"
    assert result["text"] is None
    assert result["candidates"] == 0


def test_ignores_pointer_artifact_only():
    before = Image.new("RGB", (220, 160), "white")
    after = before.copy()
    ImageDraw.Draw(after).rectangle((40, 40, 48, 48), fill="black")
    assert changed_regions(before, after, (44, 44)) == []
