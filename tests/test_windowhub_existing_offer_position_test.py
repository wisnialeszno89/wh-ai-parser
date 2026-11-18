from types import SimpleNamespace as NS

from tools import run_windowhub_existing_offer_position_test as mission


def scene(title, *, hwnd=200, elements=()):
    return NS(observation=NS(
        state=NS(active_application="Okna.exe", active_window_title=title),
        metadata={"window_handle": hwnd},
    ), elements=elements)


def button(label, automation_id="12325"):
    return NS(kind="button", label=label, metadata={
        "source": "windows_ui_automation", "automation_id": automation_id,
        "uia_visible": True, "uia_enabled": True,
    })


def native_owner(title):
    return NS(foreground=lambda: 200, parent=lambda hwnd, kind: 100, title=lambda hwnd: title)


def test_resume_requires_window_owner_of_requested_offer():
    wizard = scene("Podstawowe parametry okna")
    assert mission.belongs_to_offer(wizard, "OFR/42-", native_owner("Okna - OFR/42 <>"))
    assert not mission.belongs_to_offer(wizard, "OFR/42-", native_owner("Okna - OFR/42-99 <>"))
    assert not mission.belongs_to_offer(wizard, "OFR/42-", native_owner("Okna - ZLC/42"))


def test_finish_confirms_only_one_button_then_observes_editor(monkeypatch):
    calls = []
    before = scene("Parametry szklenia", elements=(button("Zakończ"),))
    after = scene("Modyfikator")
    monkeypatch.setattr(mission, "resolve_native_wrapper", lambda *args, **kwargs: NS(
        iface_invoke=NS(Invoke=lambda: calls.append(kwargs)),
    ))
    monkeypatch.setattr(mission, "inspect", lambda loop: after)
    assert mission.confirm_stage(object(), before, "OFR/42-", native_owner("Okna - OFR/42-")) is after
    assert calls == [{"label": "Zakończ", "automation_id": "12325", "allowed_stages": ("glazing",)}]


def test_ambiguous_confirmation_blocks_without_input(monkeypatch):
    before = scene("Podstawowe parametry okna", elements=(button("OK"), button("Zakończ", "999")))
    monkeypatch.setattr(mission, "resolve_native_wrapper", lambda *args, **kwargs: (_ for _ in ()).throw(
        AssertionError("resolver called for ambiguous buttons"),
    ))
    assert mission.confirm_stage(object(), before, "OFR/42-", native_owner("Okna - OFR/42-")) is None


def test_cli_asks_once_for_offer_and_never_for_customer(monkeypatch, capsys):
    from app.agent.runtime import windows_desktop_agent_control_loop as controls

    monkeypatch.setattr(mission, "os", NS(
        name="nt", environ={"COMPUTER_USE_LIVE": "1", "WH_REAL_WINDOWHUB": "1"},
    ))
    asked = []
    monkeypatch.setattr("builtins.input", lambda prompt: asked.append(prompt) or "OFR/42-")
    monkeypatch.setattr(controls, "create_windows_desktop_agent_control_loop", object)
    monkeypatch.setattr(mission, "_Win32Mdi", object)
    monkeypatch.setattr(mission, "run", lambda loop, offer, api: 0 if offer == "OFR/42-" else 4)
    assert mission.main(["--execute-live", "--start-delay", "0"]) == 0
    assert len(asked) == 1 and "OFR" in asked[0]
