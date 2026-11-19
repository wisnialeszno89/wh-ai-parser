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


def test_observe_only_short_prefix_never_appends_name(monkeypatch):
    import ctypes
    import sys
    from types import SimpleNamespace as NS
    from app.agent.offers import windowhub_customer_result_selection as native
    from app.agent.offers import windowhub_customer_visual_selection as visual
    from tools import run_windowhub_top_trans_single_window_mission as mission

    calls = []

    def initial(scene, prefix, **kwargs):
        calls.append(("type", prefix))
        return NS(status="search_submitted_unverified", reason="ok")

    def foreground():
        return 80

    state = NS(active_application="Okna.exe", active_window_title="Właściwości dokumentu")
    scene = NS(observation=NS(state=state, metadata={"window_handle": 80}))
    monkeypatch.setattr(ctypes, "WinDLL", lambda *a, **k: NS(GetForegroundWindow=foreground), raising=False)
    monkeypatch.setitem(sys.modules, "pywinauto.keyboard", NS(
        send_keys=lambda *a, **k: (_ for _ in ()).throw(AssertionError("typed after the short prefix")),
    ))
    monkeypatch.setattr(mission.time, "sleep", lambda seconds: None)
    monkeypatch.setattr(mission, "type_directly_into_customer_lookup", initial)
    monkeypatch.setattr(mission, "inspect", lambda loop: scene)
    monkeypatch.setattr(mission, "customer_selected", lambda *a: True)

    def scan(scene, name, **kwargs):
        calls.append(("scan", name))
        return (len(calls) == 3, "native status")

    monkeypatch.setattr(native, "select_exact_customer_result", scan)
    monkeypatch.setattr(visual, "select_exact_visual_customer", lambda *a: (False, "not visible yet"))
    result, _ = mission.progressive_customer_selection(
        object(), scene, "Top Trans Artur Janik", require_result_click=True, short_prefix_only=True,
    )
    assert result
    assert calls == [("type", "Top"), ("scan", "Top Trans Artur Janik"), ("scan", "Top Trans Artur Janik")]
