"""Incremental WindowHub customer search: check suggestions before name ends."""
from app.agent.offers.windowhub_customer_visual_selection import (
    VisualCustomerResult, match_visual_customer, popup_bounds,
)
from tools.run_windowhub_top_trans_single_window_mission import customer_typing_chunks


def test_prefix_chunks_do_not_skip_characters():
    name = "Top Trans"
    parts = customer_typing_chunks(name)
    assert "".join(parts) == name
    assert parts[0] == "Top"
    assert len(parts) > 1


def test_empty_customer_has_no_chunks():
    assert customer_typing_chunks(" ") == ()


def test_popup_region_starts_below_customer_editor():
    rect = (284, 287, 497, 309)
    region = popup_bounds(rect, (1920, 1080))
    assert region[1] > rect[3]
    assert region[0] <= rect[0]


def test_only_exact_high_confidence_customer_accepted():
    box = (300, 325, 420, 343)
    region = (250, 311, 700, 800)
    rows = [
        VisualCustomerResult("Top Trans", .94, box),
        VisualCustomerResult("Top Transport", .99, (300, 350, 470, 370)),
        VisualCustomerResult("Top Trans", .55, (300, 380, 420, 400)),
    ]
    match = match_visual_customer(rows, "Top Trans", region)
    assert len(match) == 1
    assert match[0].confidence == .94


def test_ocr_text_inside_editor_excluded():
    region = (250, 311, 700, 800)
    rows = [VisualCustomerResult("Top Trans", .99, (285, 290, 465, 307))]
    assert match_visual_customer(rows, "Top Trans", region) == []
