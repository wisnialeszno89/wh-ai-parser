"""Document core policy tests: prices may progress without risking wrong client."""
from app.agent.runtime.windowhub_document_core import PRICE_TARGETS, document_readiness


def test_document_ready_only_after_exact_customer_and_all_prices():
    assert document_readiness(customer_verified=True, flags_verified=True) == "ready"
    assert document_readiness(customer_verified=False, flags_verified=True) == "customer_unverified"
    assert document_readiness(customer_verified=True, flags_verified=False) == "pricing_unverified"


def test_requested_price_flags_construction_visible_and_services_hidden():
    assert PRICE_TARGETS == (
        ("exclude_construction_price", False),
        ("exclude_installation_price", True),
        ("exclude_removal_price", True),
        ("exclude_finishing_price", True),
    )


def test_resumed_document_can_configure_prices_without_retyping_customer(monkeypatch):
    from app.agent.runtime import windowhub_document_core as core
    from app.agent.runtime import windowhub_window_activation as activation
    from app.agent.runtime import windows_desktop_agent_control_loop as control
    from tools import run_windowhub_top_trans_single_window_mission as legacy

    class FakeState:
        active_application = "Okna.exe"
        active_window_title = "Właściwości dokumentu"

    class FakeScene:
        class Observation:
            state = FakeState()
        observation = Observation()

    scene = FakeScene()
    flags = {key: not value for key, value in PRICE_TARGETS}
    calls = []

    monkeypatch.setattr(activation, "activate_windowhub_workflow_window", lambda: (True, "ok"))
    monkeypatch.setattr(control, "create_windows_desktop_agent_control_loop", lambda: object())
    monkeypatch.setattr(legacy, "inspect", lambda loop: scene)
    monkeypatch.setattr(legacy, "customer_selected", lambda s, name: False)
    monkeypatch.setattr(
        legacy, "progressive_customer_selection",
        lambda *a, **k: (_ for _ in ()).throw(AssertionError("must not retype"))
    )
    monkeypatch.setattr(legacy, "verify_exclusion",
        lambda s, key, desired_checked=True: flags[key] is desired_checked)

    def update(scene, key, *, desired_checked=True):
        calls.append((key, desired_checked))
        flags[key] = desired_checked
        return True
    monkeypatch.setattr(legacy, "toggle_price_once", update)

    result = core.run_document_core(customer_name="Limi Fensterbau", fresh_document=False)
    assert result == 6
    assert calls == list(PRICE_TARGETS)
    assert all(flags[key] is wanted for key, wanted in PRICE_TARGETS)


def test_manual_customer_approval_resumes_only_with_exact_name_and_consent(monkeypatch):
    from app.agent.runtime import windowhub_document_core as core
    from app.agent.runtime import windowhub_window_activation as activation
    from app.agent.runtime import windows_desktop_agent_control_loop as control
    from tools import run_windowhub_top_trans_single_window_mission as legacy
    from tools import run_windowhub_new_offer_native_invoke_once as native

    class FakeState:
        active_application = "Okna.exe"
        active_window_title = "Właściwości dokumentu"

    class FakeScene:
        class Observation:
            state = FakeState()
        observation = Observation()

    scene = FakeScene()
    calls = []
    monkeypatch.setattr(activation, "activate_windowhub_workflow_window", lambda: (True, "ok"))
    monkeypatch.setattr(control, "create_windows_desktop_agent_control_loop", lambda: object())
    monkeypatch.setattr(legacy, "inspect", lambda loop: scene)
    monkeypatch.setattr(legacy, "customer_selected", lambda s, name: False)
    monkeypatch.setattr(legacy, "verify_exclusion", lambda *args, **kwargs: True)
    monkeypatch.setattr(legacy, "matches", lambda *args, **kwargs: [object()])

    def invoke():
        calls.append("OK")
        FakeState.active_window_title = "Okna - OFR/99-"

    class Wrapper:
        class Invoke:
            def Invoke(self):
                invoke()
        iface_invoke = Invoke()
    monkeypatch.setattr(native, "resolve_native_wrapper", lambda *args, **kwargs: Wrapper())

    prompts = iter(["Limi Fensterbau", "tak"])
    result = core.run_document_core(
        customer_name="Limi Fensterbau",
        fresh_document=False,
        interactive_handoff=True,
        ask=lambda prompt: next(prompts),
    )
    assert result == 0
    assert calls == ["OK"]


def test_customer_handoff_denial_leaves_dialog_open(monkeypatch):
    from app.agent.runtime import windowhub_document_core as core
    from app.agent.runtime import windowhub_window_activation as activation
    from app.agent.runtime import windows_desktop_agent_control_loop as control
    from tools import run_windowhub_top_trans_single_window_mission as legacy

    scene = type("Scene", (), {"observation": type("Observation", (), {
        "state": type("State", (), {
            "active_application": "Okna.exe",
            "active_window_title": "Właściwości dokumentu",
        })(),
    })()})()
    monkeypatch.setattr(activation, "activate_windowhub_workflow_window", lambda: (True, "ok"))
    monkeypatch.setattr(control, "create_windows_desktop_agent_control_loop", lambda: object())
    monkeypatch.setattr(legacy, "inspect", lambda loop: scene)
    monkeypatch.setattr(legacy, "customer_selected", lambda s, name: False)
    monkeypatch.setattr(legacy, "verify_exclusion", lambda *args, **kwargs: True)
    monkeypatch.setattr(legacy, "matches",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("OK must not be clicked")))
    assert core.run_document_core(
        customer_name="Limi Fensterbau", fresh_document=False,
        interactive_handoff=True, ask=lambda prompt: "nie",
    ) == 6


def test_customer_completion_prompts_for_approval_or_exact_full_name():
    from app.agent.runtime.windowhub_document_core import confirm_customer_completion

    full = "Top Trans Artur Janik"
    assert confirm_customer_completion("Top Trans", {full}, lambda prompt: "tak") == full
    assert confirm_customer_completion("Top Trans", {full}, lambda prompt: "nie") is None
    assert confirm_customer_completion("Top Trans", {full, "Top Trans Inny"}, lambda prompt: full) == full
    assert confirm_customer_completion("Top Trans", set(), lambda prompt: "Top Trans") is None


def test_customer_completion_requeries_approved_name_in_same_document(monkeypatch):
    from types import SimpleNamespace as NS
    from app.agent.runtime import windowhub_document_core as core
    from app.agent.runtime import windowhub_window_activation as activation
    from app.agent.runtime import windows_desktop_agent_control_loop as control
    from tools import run_windowhub_top_trans_single_window_mission as legacy
    from tools import run_windowhub_new_offer_native_invoke_once as native

    state = NS(active_application="Okna.exe", active_window_title="Właściwości dokumentu")
    scene = NS(observation=NS(state=state, metadata={"window_handle": 80}))
    calls = []
    monkeypatch.setattr(activation, "activate_windowhub_workflow_window", lambda: (True, "ok"))
    monkeypatch.setattr(control, "create_windows_desktop_agent_control_loop", object)
    monkeypatch.setattr(legacy, "inspect", lambda loop: scene)
    monkeypatch.setattr(legacy, "customer_selected", lambda *args: False)
    monkeypatch.setattr(legacy, "verify_exclusion", lambda *args, **kwargs: True)
    monkeypatch.setattr(legacy, "matches", lambda *args, **kwargs: [object()])

    def find(loop, scene, name, **options):
        calls.append(name)
        if len(calls) == 1:
            options["visible_completions"].add("Top Trans Artur Janik")
            assert options["short_prefix_only"] is True
            return False, "CUSTOMER_NO_EXACT_RESULT_FOR_SHORT_PREFIX"
        assert options["replace_existing"] is True
        return True, "CUSTOMER_VERIFIED_AFTER_EXACT_RESULT_CLICK"

    def confirm():
        state.active_window_title = "Okna - OFR/42-"

    monkeypatch.setattr(legacy, "progressive_customer_selection", find)
    monkeypatch.setattr(native, "resolve_native_wrapper", lambda *args, **kwargs: NS(
        iface_invoke=NS(Invoke=confirm),
    ))
    result = core.run_document_core(
        customer_name="Top Trans", fresh_document=True,
        confirm_similar_customer=True, ask=lambda prompt: "tak",
    )
    assert result == 0
    assert calls == ["Top Trans", "Top Trans Artur Janik"]


def test_blank_test_handoff_accepts_only_the_cleared_lookup(monkeypatch, capsys):
    from types import SimpleNamespace as NS
    from app.agent.runtime import windowhub_document_core as core
    from app.agent.runtime import windowhub_window_activation as activation
    from app.agent.runtime import windows_desktop_agent_control_loop as controls
    from tools import run_windowhub_top_trans_single_window_mission as legacy
    from tools import run_windowhub_new_offer_native_invoke_once as native

    state = NS(active_application="Okna.exe", active_window_title="Właściwości dokumentu")
    scene = NS(observation=NS(state=state, metadata={"window_handle": 80}))
    picker = NS(metadata={"current_value": "Top"})
    calls = []
    monkeypatch.setattr(activation, "activate_windowhub_workflow_window", lambda: (True, "ok"))
    monkeypatch.setattr(controls, "create_windows_desktop_agent_control_loop", object)
    monkeypatch.setattr(legacy, "inspect", lambda loop: scene)
    monkeypatch.setattr(legacy, "customer_selected", lambda *args: False)
    monkeypatch.setattr(legacy, "progressive_customer_selection",
                        lambda *args, **kwargs: (False, "CUSTOMER_NO_EXACT_RESULT_FOR_SHORT_PREFIX"))
    monkeypatch.setattr(legacy, "matches", lambda *args, **kwargs: [picker])
    monkeypatch.setattr(legacy, "verify_exclusion", lambda *args, **kwargs: True)

    def confirm():
        calls.append("OK")
        state.active_window_title = "Okna - OFR/42-"

    monkeypatch.setattr(native, "resolve_native_wrapper", lambda *args, **kwargs: NS(
        iface_invoke=NS(Invoke=confirm),
    ))
    kwargs = dict(
        customer_name="Top Trans", fresh_document=True, confirm_similar_customer=True,
        allow_test_blank_customer=True, ask=lambda prompt: "BEZ KLIENTA",
    )
    assert core.run_document_core(**kwargs) == 6
    assert calls == []

    picker.metadata["current_value"] = ""
    assert core.run_document_core(**kwargs) == 0
    assert calls == ["OK"]
    assert "DOCUMENT_CUSTOMER_ACCEPTANCE=human_confirmed_blank_test" in capsys.readouterr().out
