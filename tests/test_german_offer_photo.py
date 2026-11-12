import pytest

from app.agent.intake.german_offer_photo import read_german_offer_photo


def ocr_table(variant_quantity="0", second_opening="DKR"):
    lines = ["level\tleft\ttop\theight\ttext"]

    def word_line(top, text):
        for index, word in enumerate(text.split()):
            lines.append(f"5\t{index * 30}\t{top}\t16\t{word}")

    for row, (position, quantity, opening, note) in enumerate([
        ("10.0", "1", "DKL", "WkU"),
        ("11.0", variant_quantity, "DKL", "VARIANTE"),
        ("20.0", "1", second_opening, "SZ"),
    ]):
        top = 100 + row * 260
        word_line(top + 14, f"{position} {quantity} Stk. Zirkon - Fenster EP")
        word_line(top, "B: 935 mm")
        word_line(top + 28, "H: 1145 mm")
        word_line(top + 62, "F004 DK-Fenster")
        word_line(top + 88, opening)
        word_line(top + 114, f"Abdeckstreifen: Aluminium auBen, {3 if row == 0 else 4}-seitig, 2x30mm")
        word_line(top + 164, note)
    return "\n".join(lines)


def test_photo_preserves_positions_and_omits_zero_quantity_variant():
    draft = read_german_offer_photo(ocr_table())
    left, right = draft["positions"]

    assert (left["position"], left["opening"], left["note_code"]) == ("10.0", "DKL", "WKÜ")
    assert (right["position"], right["opening"], right["note_code"]) == ("20.0", "DKR", "SZ")
    assert (left["width_mm"], left["height_mm"]) == (935, 1145)
    assert (left["cover_strip"]["sides"], right["cover_strip"]["sides"]) == (3, 4)
    assert draft["excluded"] == [{"position": "11.0", "reason": "zero_quantity"}]


@pytest.mark.parametrize(("options", "position"), [
    ({"variant_quantity": "1"}, "11.0"),
    ({"second_opening": "DK?"}, "20.0"),
])
def test_photo_requires_review_for_unverified_active_positions(options, position):
    with pytest.raises(ValueError, match=f"Pozycja {position}"):
        read_german_offer_photo(ocr_table(**options))
