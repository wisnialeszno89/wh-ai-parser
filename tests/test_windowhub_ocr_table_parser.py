from types import SimpleNamespace

from app.agent.perception.windowhub_ocr_table_parser import parse_windowhub_ocr_table


def element(label, x, center_y, confidence=0.99):
    return SimpleNamespace(label=label, x=x, y=center_y - 4, width=40, height=8, confidence=confidence)


def make_row(number, center_y, *, include_lp=True):
    values = [
        element("1 Okno", 210, center_y),
        element("1.234,56", 420, center_y),
        element("793,35", 530, center_y),
        element("1320x1345", 1120, center_y),
    ]
    if include_lp:
        values.append(element(str(number), 120, center_y))
    return values


def test_parses_lp_quantity_article_prices_and_dimensions():
    rows = parse_windowhub_ocr_table(make_row(1, 223.9))
    assert len(rows) == 1
    row = rows[0]
    assert row.lp == 1
    assert row.quantity == 1
    assert row.article == "Okno"
    assert row.gross_total == "1234.56"
    assert row.gross_unit == "793.35"
    assert row.dimensions == "1320 x 1345"
    assert row.complete


def test_falls_back_to_price_anchor_without_guessing_lp():
    rows = parse_windowhub_ocr_table(make_row(1, 223.9, include_lp=False))
    assert len(rows) == 1
    assert rows[0].lp is None
    assert rows[0].lp_source == "price_column_row_order"
    assert "lp" in rows[0].missing_fields
    assert not rows[0].complete


def test_deduplicates_duplicate_lp_detections_at_same_height():
    items = make_row(2, 238.2) + [element("2", 121, 239.1)]
    rows = parse_windowhub_ocr_table(items)
    assert len(rows) == 1
    assert rows[0].lp == 2


def test_low_confidence_lp_does_not_become_authoritative_anchor():
    items = make_row(1, 223.9, include_lp=False) + [element("1", 120, 223.9, confidence=0.1)]
    rows = parse_windowhub_ocr_table(items)
    assert len(rows) == 1
    assert rows[0].lp is None
    assert "lp" in rows[0].missing_fields


def test_ignores_malformed_elements_and_invalid_boxes():
    items = make_row(1, 223.9) + [object(), SimpleNamespace(label="2", x=None, y=None, height=None)]
    rows = parse_windowhub_ocr_table(items)
    assert len(rows) == 1
    assert rows[0].complete


def test_dimension_parser_accepts_multiplication_symbol():
    rows = parse_windowhub_ocr_table([
        element("1 Okno", 210, 223.9),
        element("100,00", 420, 223.9),
        element("100,00", 530, 223.9),
        element("810×1325", 1120, 223.9),
    ], anchor_x_max=-1)
    assert rows[0].dimensions == "810 x 1325"


def test_empty_input_returns_no_rows():
    assert parse_windowhub_ocr_table([]) == ()
