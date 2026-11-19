from types import SimpleNamespace as NS

import pytest

from tools import run_windowhub_two_position_live as live


def scene(title, *, hwnd=200, elements=()):
    return NS(
        observation=NS(
            state=NS(active_application="Okna.exe", active_window_title=title),
            metadata={"window_handle": hwnd},
        ),
        elements=elements,
    )


def owner(title):
    return NS(foreground=lambda: 200, parent=lambda hwnd, kind: 100, title=lambda hwnd: title)


def edit(label="Rabat [%]", automation_id="100"):
    return NS(kind="edit", label=label, metadata={
        "source": "windows_ui_automation", "uia_enabled": True, "uia_visible": True,
        "automation_id": automation_id, "uia_runtime_id": automation_id, "name": label,
    })


def test_discount_checks_foreground_offer_and_exact_field():
    modal = scene("Wycena", elements=(edit(), edit("Cena", "101")))
    assert live.owned_discount(modal, "OFR/42-", owner("Okna - OFR/42-"))
    assert not live.owned_discount(modal, "OFR/42-", owner("Okna - OFR/43-"))
    assert not live.owned_discount(modal, "OFR/42-", owner("Okna - ZLC/42-"))
    assert live.discount_field(modal).label == "Rabat [%]"
    assert live.discount_field(scene("Rabat", elements=(edit(), edit("Rabat", "101")))) is None
    assert not live.owned_discount(scene("Rabat", hwnd=201), "OFR/42-", owner("Okna - OFR/42-"))


@pytest.mark.parametrize(("value", "valid"), [
    ("18", True), ("18,00 %", True), ("18.0%", True),
    ("18.01", False), ("0.18", False), ("180", False), ("18 PLN", False), (None, False),
])
def test_native_discount_value_readback(value, valid):
    assert live.discount_is_18(value) is valid


def test_discount_writes_once_and_confirms_only_after_fresh_readback(monkeypatch):
    api = owner("Okna - OFR/42-")
    before, readback = scene("Rabat"), scene("Rabat")
    after = scene("Dodawanie nowej pozycji")
    calls = []
    edited = NS(CurrentValue="0", CurrentIsReadOnly=False, SetValue=lambda v: calls.append(("set", v)))

    def read(current, offer, native):
        calls.append(("read", current))
        return edited if current is before else NS(CurrentValue="18,00%")

    def confirm(current, labels, *, still_owned):
        assert still_owned() and current is readback and "ok" in labels
        calls.append(("confirm", current))
        return True

    monkeypatch.setattr(live, "read_discount", read)
    monkeypatch.setattr(live, "inspect", lambda loop: readback)
    monkeypatch.setattr(live, "invoke_confirmation", confirm)
    monkeypatch.setattr(live, "refresh_transition", lambda *a, **kw: after)
    assert live.complete_discount(object(), before, "OFR/42-", api) is after
    assert calls == [("read", before), ("set", "18"), ("read", readback), ("confirm", readback)]


def test_discount_wrong_readback_stops_without_confirmation(monkeypatch):
    modal = scene("Rabat")
    api = owner("Okna - OFR/42-")
    monkeypatch.setattr(live, "read_discount", lambda *a: NS(CurrentValue="15", CurrentIsReadOnly=True))
    monkeypatch.setattr(live, "inspect", lambda loop: modal)
    monkeypatch.setattr(live, "ask_ready", lambda prompt: False)
    monkeypatch.setattr(live, "invoke_confirmation", lambda *a, **kw: pytest.fail("unverified discount"))
    assert live.complete_discount(object(), modal, "OFR/42-", api) is None


def setup_flow(monkeypatch):
    calls = []
    document = scene("Okna - OFR/42-")
    discount = scene("Rabat")
    position = scene("Dodawanie nowej pozycji")
    monkeypatch.setattr(live, "belongs_to_offer", lambda *a: True)
    monkeypatch.setattr(live, "run", lambda *a, **kw: calls.append(("wizard", kw["width"])) or 0)
    monkeypatch.setattr(live, "build_and_confirm", lambda *a: calls.append(("build", a[-1])) or document)
    monkeypatch.setattr(live, "open_next", lambda *a: calls.append(("add", 2)) or discount)
    monkeypatch.setattr(live, "complete_discount", lambda *a: calls.append(("discount", 18)) or position)
    monkeypatch.setattr(live, "ask_ready", lambda prompt: True)
    monkeypatch.setattr(live, "refresh_transition", lambda *a, **kw: document)
    return calls, document, position


def test_offer_constructs_second_only_after_discount(monkeypatch):
    calls, _, _ = setup_flow(monkeypatch)
    assert live.run_offer(object(), "OFR/42-", owner("Okna - OFR/42-")) == 0
    assert calls == [
        ("wizard", 1000), ("build", 1), ("add", 2), ("discount", 18),
        ("wizard", 1500), ("build", 2),
    ]


def test_offer_never_dispatches_add_twice_after_uncertain_transition(monkeypatch):
    calls, document, position = setup_flow(monkeypatch)
    monkeypatch.setattr(live, "complete_discount", lambda *a: document)
    monkeypatch.setattr(live, "handoff_scene", lambda *a, **kw: position)
    assert live.run_offer(object(), "OFR/42-", owner("Okna - OFR/42-")) == 0
    assert calls.count(("add", 2)) == 1


def test_offer_blocks_second_wizard_when_discount_unknown(monkeypatch):
    calls, _, _ = setup_flow(monkeypatch)
    monkeypatch.setattr(live, "complete_discount", lambda *a: None)
    assert live.run_offer(object(), "OFR/42-", owner("Okna - OFR/42-")) == 4
    assert calls == [("wizard", 1000), ("build", 1), ("add", 2)]


def test_requested_geometry_runs_through_existing_construction_lab():
    from app.agent.offers.windowhub_offer_workflow_lab import OfferWorkflowLab

    first, second = live.POSITIONS
    workflow = OfferWorkflowLab()
    workflow.new_offer()
    workflow.confirm_document(dict(
        customer="Top Trans", confirmed=True, construction=False,
        installation=True, removal=True, finishing=True,
    ))
    for index, (position, kind, spec) in enumerate((
        (first, "single", {"opening": first.left_opening}),
        (second, "double_fixed", {
            "mullion": "fixed", "split_from_left_mm": second.split_from_left_mm,
            "left_opening": second.left_opening, "right_opening": second.right_opening,
        }),
    )):
        if index:
            workflow.next_position()
        workflow.select_window(kind)
        workflow.set_dimensions(1, position.width, position.height)
        workflow.set_color("biały", "antracyt")
        workflow.build({**spec, "glazing_panes": 3})
        workflow.add_position()
    rows = workflow.save()["positions"]
    assert rows[0]["specification"] == {"opening": "DKL", "glazing_panes": 3}
    assert rows[1]["specification"] == {
        "mullion": "fixed", "split_from_left_mm": 750,
        "left_opening": "DKL", "right_opening": "DKR", "glazing_panes": 3,
    }
