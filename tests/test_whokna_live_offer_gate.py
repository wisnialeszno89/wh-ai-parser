"""Pure safety gate regressions for live-guided WindowHub preflight."""
import pytest

from app.agent.knowledge.whokna_live_offer_gate import check_offer_scene


@pytest.mark.parametrize("title,stage", [
    ("Okna - OFR/4708-", "offer_document"),
    ("Okna - Start1", "start"),
    ("Dodawanie nowej pozycji", "wizard"),
    ("Wielkość okna", "wizard"),
])
def test_valid_observed_offer_stages(title, stage):
    gate = check_offer_scene(
        process="Okna.exe", title=title, has_window_rect=True,
        has_image=True, observed_elements=20,
    )
    assert gate.ok and gate.scene_stage == stage


@pytest.mark.parametrize("process,title", [
    ("code.exe", "Okna - OFR/4708-"),
    ("Okna.exe", "Okna - ZLC/4708-"),
    ("Okna.exe", "Wybór okuć: 1"),
    ("Okna.exe", "Bez nazwy"),
])
def test_wrong_or_unsafe_stage_stops(process, title):
    gate = check_offer_scene(
        process=process, title=title, has_window_rect=True,
        has_image=True, observed_elements=20,
    )
    assert not gate.ok


def test_missing_screenshot_and_elements_fail_closed():
    gate = check_offer_scene(
        process="Okna.exe", title="Okna - OFR/4708-",
        has_window_rect=True, has_image=False, observed_elements=0,
    )
    assert not gate.ok
