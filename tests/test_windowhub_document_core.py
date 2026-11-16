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
