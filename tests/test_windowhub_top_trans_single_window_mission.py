"""Mission boundaries: exact customer, exact requested prices, no implicit live input."""
from types import SimpleNamespace

from tools import run_windowhub_top_trans_single_window_mission as mission


def elem(kind, label, automation_id, *, value=None, checked=None, visible=True):
    return SimpleNamespace(
        kind=kind, label=label,
        metadata={
            "source": "windowhub_ui_automation",
            "automation_id": automation_id,
            "uia_visible": visible, "uia_enabled": True,
            "current_value": value, "uia_checked": checked,
        },
    )


def scene(*elements):
    return SimpleNamespace(elements=elements)


def test_requested_customer_is_exact_top_trans():
    assert mission.CUSTOMER == "Top Trans"
    assert mission.TARGET["quantity"] == 1
    assert mission.TARGET["color"] == "antracyt"
    assert mission.TARGET["glazing"] == "triple"
    assert mission.TARGET["opening"] == "RU"


def test_only_three_requested_price_exclusions():
    assert mission.EXCLUSIONS == (
        "exclude_installation_price",
        "exclude_removal_price",
        "exclude_finishing_price",
    )
    assert "exclude_construction_price" not in mission.EXCLUSIONS


def test_does_not_accept_any_other_customer_or_selection_focus():
    wrong = elem("button", "Wybierz istniejącego klienta", "IDC_ZAMAWIAJACY",
                 value="Top Trans S.A.")
    exact = elem("button", "Wybierz istniejącego klienta", "IDC_ZAMAWIAJACY",
                 value="Top Trans")
    assert mission.customer_selected(scene(wrong)) is False
    assert mission.customer_selected(scene(exact)) is True
    assert mission.customer_selected(scene(wrong, exact)) is True


def test_price_state_must_be_confirmed_checked():
    box = elem("checkbox", "Bez ceny montażu", "IDC_CENA_MONTAZU", checked=False)
    assert not mission.verify_exclusion(scene(box), "exclude_installation_price")
    box.metadata["uia_checked"] = True
    assert mission.verify_exclusion(scene(box), "exclude_installation_price")


def test_duplicate_checked_controls_do_not_pass():
    a = elem("checkbox", "Bez ceny montażu", "IDC_CENA_MONTAZU", checked=True)
    b = elem("checkbox", "Bez ceny montażu", "IDC_CENA_MONTAZU", checked=True)
    assert not mission.verify_exclusion(scene(a, b), "exclude_installation_price")


def test_no_live_flags_means_no_action(monkeypatch):
    monkeypatch.delenv("WH_REAL_WINDOWHUB", raising=False)
    monkeypatch.delenv("COMPUTER_USE_LIVE", raising=False)
    assert mission.main(["--execute-live"]) == 2
