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
    assert row.total_value == "1234.56"
    assert row.unit_value == "793.35"
    assert row.dimensions == "1320 x 1345"
    assert row.complete


def test_uses_unit_price_anchor_when_total_value_ocr_is_missing():
    items = [
        element("1 Okno", 210, 223.9),
        element("793,35", 530, 223.9),
        element("1320x1345", 1120, 223.9),
        element("4", 120, 223.9),
    ]

    rows = parse_windowhub_ocr_table(items)

    assert len(rows) == 1
    assert rows[0].lp == 4
    assert rows[0].total_value is None
    assert rows[0].unit_value == "793.35"
    assert rows[0].dimensions == "1320 x 1345"
    assert "total_value" in rows[0].missing_fields


def test_unit_price_anchor_adds_row_when_only_that_rows_total_is_missing():
    items = [
        element("1 Okno", 210, 223.0),
        element("1000,00", 420, 223.0),
        element("800,00", 530, 223.0),
        element("1200x1350", 1120, 223.0),
        element("1", 120, 223.0),
        element("1 Okno", 210, 238.0),
        element("795,00", 530, 238.0),
        element("1300x1350", 1120, 238.0),
        element("2", 120, 238.0),
        element("1 Okno", 210, 253.0),
        element("1010,00", 420, 253.0),
        element("810,00", 530, 253.0),
        element("1400x1350", 1120, 253.0),
        element("3", 120, 253.0),
    ]

    rows = parse_windowhub_ocr_table(items)

    assert len(rows) == 3
    assert [row.lp for row in rows] == [1, 2, 3]
    assert [row.total_value for row in rows] == ["1000.00", None, "1010.00"]
    assert [row.unit_value for row in rows] == ["800.00", "795.00", "810.00"]
    assert [row.row_index for row in rows] == [1, 2, 3]


def test_keeps_missing_total_row_when_unit_price_is_near_previous_row():
    # The middle row has no total-price OCR. Its unit-price detection is shifted
    # upward and falls within row_tolerance of the previous total anchor, while
    # LP/article/dimensions detections independently cluster nearer that unit
    # token. It must remain a separate row instead of disappearing.
    items = [
        element("1 Okno", 210, 223.0),
        element("1000,00", 420, 223.0),
        element("800,00", 530, 223.0),
        element("1200x1350", 1120, 223.0),
        element("1", 120, 223.0),

        element("1 Okno", 210, 237.0),
        element("795,00", 530, 230.0),
        element("1300x1350", 1120, 237.0),
        element("2", 120, 237.0),

        element("1 Okno", 210, 251.0),
        element("1010,00", 420, 251.0),
        element("810,00", 530, 251.0),
        element("1400x1350", 1120, 251.0),
        element("3", 120, 251.0),
    ]

    rows = parse_windowhub_ocr_table(items)

    assert len(rows) == 3
    assert [row.lp for row in rows] == [1, 2, 3]
    assert [row.total_value for row in rows] == ["1000.00", None, "1010.00"]
    assert [row.unit_value for row in rows] == ["800.00", "795.00", "810.00"]
    assert [row.article for row in rows] == ["Okno", "Okno", "Okno"]
    assert [row.dimensions for row in rows] == [
        "1200 x 1350", "1300 x 1350", "1400 x 1350"
    ]



def test_does_not_create_extra_row_from_vertical_drift_across_price_columns():
    # The unit prices for two distinct rows land only three pixels apart.
    # Row anchors and the other columns make it safe to assign them separately.
    items = [
        element("1 Okno", 210, 223.0),
        element("1000,00", 420, 223.0),
        element("800,00", 530, 227.0),
        element("1200x1350", 1120, 223.0),
        element("1", 120, 223.0),

        element("1 Okno", 210, 237.0),
        element("995,00", 420, 237.0),
        element("795,00", 530, 230.0),
        element("1300x1350", 1120, 237.0),
        element("2", 120, 237.0),

        element("1 Okno", 210, 251.0),
        element("1010,00", 420, 251.0),
        element("810,00", 530, 255.0),
        element("1400x1350", 1120, 251.0),
        element("3", 120, 251.0),
    ]

    rows = parse_windowhub_ocr_table(items)

    assert len(rows) == 3
    assert [row.lp for row in rows] == [1, 2, 3]
    assert [row.total_value for row in rows] == [
        "1000.00", "995.00", "1010.00"
    ]
    assert [row.unit_value for row in rows] == [
        "800.00", "795.00", "810.00"
    ]


def test_ambiguous_unit_price_between_rows_is_not_guessed():
    items = [
        element("1 Okno", 210, 223.0),
        element("1000,00", 420, 223.0),
        element("1200x1350", 1120, 223.0),
        element("1", 120, 223.0),
        element("1 Okno", 210, 237.0),
        element("995,00", 420, 237.0),
        element("1300x1350", 1120, 237.0),
        element("2", 120, 237.0),
        # Exactly halfway between the two row anchors, with no other unit
        # price token to establish which row it belongs to.
        element("795,00", 530, 230.0),
    ]

    rows = parse_windowhub_ocr_table(items)

    assert len(rows) == 2
    assert [row.unit_value for row in rows] == [None, None]


def test_prefers_total_price_anchor_when_both_price_columns_are_detected():
    items = [
        element("1 Okno", 210, 223.0),
        element("1000,00", 420, 223.0),
        # Slight vertical drift from OCR in the unit-price column.
        element("800,00", 530, 227.0),
        element("1200x1350", 1120, 223.0),
        element("1", 120, 223.0),
    ]

    rows = parse_windowhub_ocr_table(items)

    assert len(rows) == 1
    assert rows[0].center_y == 223.0
    assert rows[0].total_value == "1000.00"
    assert rows[0].unit_value == "800.00"


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


def test_dimension_parser_accepts_ocr_confused_multiplication_separator():
    rows = parse_windowhub_ocr_table([
        element("1 Okno", 210, 223.9),
        element("100,00", 420, 223.9),
        element("100,00", 530, 223.9),
        element("1000Î1000", 1120, 223.9),
    ], anchor_x_max=-1)
    assert rows[0].dimensions == "1000 x 1000"


def test_empty_input_returns_no_rows():
    assert parse_windowhub_ocr_table([]) == ()

def test_payload_uses_screen_column_semantics_not_gross_labels():
    rows = parse_windowhub_ocr_table(make_row(1, 223.9))
    payload = rows[0].to_payload()
    assert payload["total_value"] == "1234.56"
    assert payload["unit_value"] == "793.35"
    assert "gross_total" not in payload
    assert "gross_unit" not in payload


def test_adapts_shifted_price_columns_ignores_montage_and_keeps_ninth_row():
    centers = (224.0, 241.0, 258.0, 276.0, 293.0, 309.0, 326.0, 344.0, 361.0)
    items = []
    expected_total = []
    expected_unit = []
    for index, center_y in enumerate(centers, start=1):
        total = f"{1000 + index},00"
        unit = f"{800 + index},00"
        expected_total.append(f"{1000 + index}.00")
        expected_unit.append(f"{800 + index}.00")
        items.extend([
            element("1 Okno" if index == 1 else "Okno", 210, center_y),
            element(total, 365, center_y),
            element(unit, 464, center_y),
            element("0,00", 551, center_y),  # A later Montage column, not unit value.
            element(f"{1200 + index}x1350", 1280, center_y),
            element(str(index), 120, center_y),
        ])

    rows = parse_windowhub_ocr_table(items)

    assert len(rows) == 9
    assert [row.lp for row in rows] == list(range(1, 10))
    assert [row.total_value for row in rows] == expected_total
    assert [row.unit_value for row in rows] == expected_unit
    assert all(row.article == "Okno" for row in rows)
    assert rows[0].quantity == 1
    assert all(row.dimensions == f"{1200 + i} x 1350" for i, row in enumerate(rows, 1))
