from decimal import Decimal
from types import SimpleNamespace as NS

import pytest

from app.agent.runtime import windowhub_pricing_dialog as pricing
from tools import run_windowhub_autonomous_offer as live


@pytest.mark.parametrize(("text", "expected"), [
    ("0,00%", Decimal(0)), (" 18,50 %", Decimal("18.50")), ("100", Decimal(100)),
    ("NaN", None), ("-18", None), ("100,01%", None), ("0,001%", None), ("", None),
])
def test_discount_readback(text, expected):
    assert pricing.parse_discount(text) == expected


def test_discount_association_uses_label_and_adjacent_row():
    def control(name, left, top, width):
        return NS(name=name, rectangle=lambda: NS(left=left, right=left+width, top=top, bottom=top+24))

    caption = control("-- Rabat [%]", 150, 144, 100)
    markup = control("", 260, 115, 100)
    discount = control("", 260, 144, 100)
    vat = control("", 260, 173, 100)
    price = control("", 460, 144, 100)
    name = lambda item: item.name
    assert pricing.discount_control([markup, discount, vat, price], [caption], name) is discount
    assert pricing.discount_control([discount, control("", 300, 144, 40)], [caption], name) is None


@pytest.mark.parametrize(("existing", "requested", "writes"), [
    ("0,00%", Decimal(0), []),
    ("18,00%", Decimal(0), ["0"]),
    ("0,00%", Decimal("18.5"), ["18,5"]),
])
def test_approve_after_exact_readback(monkeypatch, existing, requested, writes):
    values, actions = [existing], []

    def write(value):
        values[0] = value
        actions.append(value)

    monkeypatch.setattr(pricing, "native_pricing_controls", lambda hwnd: (
        lambda: values[0], write, lambda: actions.append("accept"),
    ))
    assert pricing.confirm_position_pricing(123, requested, still_owned=lambda: True)
    assert actions == [*writes, "accept"]


def test_stale_or_unapplied_discount_never_approves(monkeypatch):
    clicks = []
    monkeypatch.setattr(pricing, "native_pricing_controls", lambda hwnd: (
        lambda: "13,00%", lambda value: None, lambda: clicks.append(hwnd),
    ))
    assert not pricing.confirm_position_pricing(123, Decimal(0), still_owned=lambda: True)
    assert not pricing.confirm_position_pricing(123, Decimal(13), still_owned=lambda: False)
    assert clicks == []


def test_pricing_is_accepted_once_and_waits_for_same_draft_wizard(monkeypatch, capsys):
    scope = NS(frame=10, child=20, pid=50)
    frames = iter([30, 30, 40])
    foreground = [0]
    api = NS(
        foreground=lambda: foreground[0], pid=lambda _: 50,
        title=lambda hwnd: pricing.PRICING_TITLE if hwnd == 30 else "Dodawanie nowej pozycji",
        parent=lambda hwnd, kind: 10, owner=lambda hwnd: 0,
    )

    def observe(loop):
        foreground[0] = next(frames)
        return foreground[0]

    actions = []
    monkeypatch.setattr(live, "inspect", observe)
    monkeypatch.setattr(live, "foreground_handle", lambda scene, api: scene)
    monkeypatch.setattr(live, "active_mdi_child", lambda *args: 20)
    monkeypatch.setattr(live, "stage_of", lambda scene: "position" if scene == 40 else "windowhub_unmapped")
    monkeypatch.setattr(live, "confirm_position_pricing", lambda hwnd, rate, still_owned: (
        actions.append((hwnd, rate)) or still_owned()
    ))
    monkeypatch.setattr(live.time, "sleep", lambda _: None)
    assert live.wait_for_next_wizard(None, scope, api, Decimal(0)) == 40
    assert actions == [(30, Decimal(0))]
    assert "WH_PRICING_TRANSITION=position" in capsys.readouterr().out


def test_resume_requires_named_native_test_draft(monkeypatch):
    foreground = 30
    captions = {10: "Okna -", 20: "Dokument13", 30: pricing.PRICING_TITLE}
    api = NS(foreground=lambda: foreground, pid=lambda _: 50, title=captions.__getitem__,
             parent=lambda h, k: 10 if h == 30 else h, owner=lambda h: 10 if h == 30 else 0)
    scene = NS(observation=NS(metadata={"window_handle": 30}))
    monkeypatch.setattr(live, "stage_of", lambda _: "windowhub_unmapped")
    monkeypatch.setattr(live, "active_mdi_child", lambda frame, _: 20 if frame == 10 else 0)
    assert live.bind_draft_pricing(scene, api, "Dokument13").child == 20
    assert live.bind_draft_pricing(scene, api, "Dokument15") is None
    captions[20] = "OFR/42-"
    assert live.bind_draft_pricing(scene, api, "active") is None


def test_blank_position_is_verified_without_mutating_construction(monkeypatch):
    progress = live.OfferProgress()
    monkeypatch.setattr(live, "observe_workspace", lambda *a, **kw: (None, None, None, None, "empty"))
    monkeypatch.setattr(live, "build_construction", lambda *a, **kw: pytest.fail("blank must not be built"))
    live.finish_position(None, None, None, 1, (1000, 1000), opening=True, blank=True, progress=progress)
    assert progress.report()["partial_count"] == 1
    assert progress.report()["complete_count"] == 0


def test_placeholder_refuses_existing_construction(monkeypatch):
    monkeypatch.setattr(live, "observe_workspace", lambda *a, **kw: (None, None, None, None, "frame"))
    with pytest.raises(live.WorkspaceBlocked, match="placeholder_not_empty"):
        live.finish_position(None, None, None, 1, (1000, 1000), opening=True, blank=True, progress=None)
