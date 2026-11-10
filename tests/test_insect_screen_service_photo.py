from PIL import Image, ImageDraw
import pytest

from app.agent.intake import insect_screen_service_photo as service


def test_service_photo_selects_only_marked_items_and_keeps_measurements_open(monkeypatch, tmp_path):
    path = tmp_path / "synthetic.png"
    image = Image.new("RGB", (450, 300), "white")
    draw = ImageDraw.Draw(image)
    for top in (116, 181):
        draw.line((186, top, 204, top + 20), fill="navy", width=2)
        draw.line((204, top, 186, top + 20), fill="navy", width=2)
    image.save(path)
    header = [(x, 10, 20, 10, label) for x, label in [
        (15, "Pos."), (45, "Anzahl"), (80, "Einheit"), (155, "Artikelnr."), (205, "Bezeichnung"),
    ]] + [(15, 270, 30, 10, "Summe")]
    items = [
        (x, y, 15, 25, word)
        for y, row in [(75, "1 2 Stk. 00009"), (270, "2 5 Stk. 00004"), (465, "3 3 Stk. 00003")]
        for x, word in enumerate(row.split())
    ]
    descriptions = [
        [(0, 0, 30, 10, text)]
        for text in ("Fenster Insektenschutzgitter 1510 x 1490mm", "Fenster Insektenschutzrollo 780 x 1490mm")
    ]
    readings = iter([header, items, *descriptions])
    monkeypatch.setattr(service.shutil, "which", lambda _: "tesseract")
    monkeypatch.setattr(service, "_ocr", lambda *args: next(readings))

    draft = service.read_insect_screen_service_photo(path)

    assert draft["status"] == "sales_review_required"
    assert [
        (row["position"], row["quantity"], row["screen_type"], row["source_window_width_mm"],
         row["source_window_height_mm"])
        for row in draft["positions"]
    ] == [("2", 5, None, 1510, 1490), ("3", 3, "roller", 780, 1490)]
    for row in draft["positions"]:
        assert row["price"] is row["order_width_mm"] is row["order_height_mm"] is None


def test_blue_ink_without_a_cross_requires_review():
    image = Image.new("RGB", (50, 50), "white")
    assert not service._blue_cross(image, (0, 0, 50, 50), 10)
    ImageDraw.Draw(image).line((8, 8, 28, 28), fill="navy", width=2)
    with pytest.raises(ValueError, match="Niejednoznaczne"):
        service._blue_cross(image, (0, 0, 50, 50), 10)
