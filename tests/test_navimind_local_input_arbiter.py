"""Threaded, portable input arbitration tests without real desktop access."""
from __future__ import annotations

from threading import Event, Thread
import pytest

from app.agent.runtime.navimind_local_input_arbiter import (
    ActionPermit, InputDenied, InputOwner, LocalInputArbiter,
)


def setup():
    gate = LocalInputArbiter()
    permit = gate.observe_document("OFR/1")
    return gate, permit


def test_fresh_permit_dispatches_exactly_one_operation():
    gate, permit = setup()
    called = []
    assert gate.dispatch(permit, lambda: called.append("click") or "ok") == "ok"
    assert called == ["click"]
    assert gate.owner == InputOwner.AGENT


def test_human_takeover_revokes_all_queued_actions():
    gate, permit = setup()
    gate.takeover()
    assert gate.owner == InputOwner.HUMAN
    with pytest.raises(InputDenied):
        gate.dispatch(permit, lambda: pytest.fail("input executed"))
    assert gate.reobservation_required


def test_after_release_old_permit_is_still_invalid():
    gate, permit = setup()
    gate.takeover()
    gate.release()
    assert gate.owner == InputOwner.AGENT
    assert not gate.permit_current(permit)
    with pytest.raises(InputDenied):
        gate.dispatch(permit, lambda: pytest.fail("stale input"))
    fresh = gate.observe_document("OFR/1")
    assert fresh.epoch != permit.epoch
    assert gate.dispatch(fresh, lambda: "resumed") == "resumed"


def test_automatic_resume_requires_new_verified_document():
    gate, _ = setup()
    gate.takeover()
    gate.release()
    assert gate.reobservation_required
    with pytest.raises(InputDenied, match="verified_document_key_required"):
        gate.observe_document("")
    with pytest.raises(InputDenied):
        gate.dispatch(ActionPermit(gate.epoch, "OFR/1"), lambda: None)


def test_wrong_offer_permit_does_not_dispatch():
    gate, permit = setup()
    invalid = ActionPermit(permit.epoch, "OFR/OTHER")
    with pytest.raises(InputDenied):
        gate.dispatch(invalid, lambda: pytest.fail("wrong offer"))


def test_new_observation_invalidates_prior_decision():
    gate, old = setup()
    gate.invalidate_observation()
    with pytest.raises(InputDenied):
        gate.dispatch(old, lambda: pytest.fail("old observation"))
    current = gate.observe_document("OFR/2")
    assert gate.dispatch(current, lambda: True)


def test_takeover_during_native_action_finishes_atomic_step_then_blocks_more():
    gate, permit = setup()
    entered, allow_end, takeover_started = Event(), Event(), Event()
    seen = []

    def native_action():
        entered.set()
        assert allow_end.wait(timeout=3)
        seen.append("native_done")

    doing = Thread(target=lambda: gate.dispatch(permit, native_action))
    doing.start()
    assert entered.wait(timeout=3)

    def takeover():
        takeover_started.set()
        gate.takeover()
        seen.append("human_owns")

    human = Thread(target=takeover)
    human.start()
    assert takeover_started.wait(timeout=3)
    # Tk can read owner and epoch and revoke the permit while Windows is blocked.
    human.join(timeout=1)
    assert not human.is_alive()
    assert gate.owner == InputOwner.HUMAN
    assert gate.epoch > permit.epoch
    assert not gate.permit_current(permit)
    with pytest.raises(InputDenied, match="human_takeover_requested"):
        gate.dispatch(permit, lambda: pytest.fail("queued agent input"))
    new_epoch = gate.release()
    with pytest.raises(InputDenied, match="native_dispatch_in_progress"):
        gate.dispatch_pending_navigation(new_epoch, lambda: pytest.fail("concurrent native action"))
    allow_end.set()
    doing.join(timeout=3)
    human.join(timeout=3)
    assert not doing.is_alive() and not human.is_alive()
    assert seen == ["human_owns", "native_done"]
    assert gate.dispatch_pending_navigation(new_epoch, lambda: "recovered") == "recovered"


def test_takeover_during_planning_prevents_action_even_before_epoch_changes():
    gate, permit = setup()
    gate._takeover_requested.set()
    with pytest.raises(InputDenied, match="human_takeover_requested"):
        gate.dispatch(permit, lambda: pytest.fail("planned action executed"))
    gate.takeover()
    assert gate.owner == InputOwner.HUMAN


def test_cannot_release_without_human_ownership():
    gate = LocalInputArbiter()
    with pytest.raises(InputDenied, match="release_requires_human_ownership"):
        gate.release()


def test_repeated_takeover_release_keeps_old_permits_invalid():
    gate, permit = setup()
    for _ in range(3):
        gate.takeover()
        gate.release()
    assert gate.epoch == 6
    assert not gate.permit_current(permit)


def test_operation_exception_does_not_leak_native_lock():
    gate, permit = setup()

    def fail():
        raise RuntimeError("native operation error")

    with pytest.raises(RuntimeError):
        gate.dispatch(permit, fail)
    gate.takeover()
    assert gate.owner == InputOwner.HUMAN


def test_invalid_or_fabricated_permit_is_rejected():
    gate, permit = setup()
    for forged in (None, "OFR/1", ActionPermit(True, "OFR/1"),
                   ActionPermit(permit.epoch + 1, "OFR/1")):
        with pytest.raises(InputDenied):
            gate.dispatch(forged, lambda: pytest.fail("forged"))


def test_human_takeover_does_not_grant_business_save_permission():
    gate, permit = setup()
    # The gate handles ownership, not WindowHub business semantics.
    assert gate.dispatch(permit, lambda: "synthetic test") == "synthetic test"
    assert not hasattr(gate, "approve_save")
    assert not hasattr(gate, "send_offer")


def test_forged_same_epoch_document_key_without_issue_nonce_is_rejected():
    gate, permit = setup()
    forged = ActionPermit(permit.epoch, permit.document_key)
    assert not gate.permit_current(forged)
    with pytest.raises(InputDenied):
        gate.dispatch(forged, lambda: pytest.fail("forged input must be blocked"))


def test_renewed_observation_replaces_same_epoch_permit_nonce():
    gate, first = setup()
    second = gate.observe_document("OFR/1")
    assert first.epoch == second.epoch
    assert first.nonce != second.nonce
    assert not gate.permit_current(first)
    assert gate.permit_current(second)


def test_start_navigation_requires_the_current_pending_operator_epoch():
    gate, _ = setup()
    gate.takeover()
    with pytest.raises(InputDenied):
        gate.dispatch_pending_navigation(gate.epoch, lambda: pytest.fail("human owns input"))

    epoch = gate.release()
    assert gate.dispatch_pending_navigation(epoch, lambda: "start1") == "start1"
    gate.observe_document("DRAFT/NEW")
    with pytest.raises(InputDenied):
        gate.dispatch_pending_navigation(epoch, lambda: pytest.fail("document already observed"))

    gate.takeover()
    gate.release()
    with pytest.raises(InputDenied):
        gate.dispatch_pending_navigation(epoch, lambda: pytest.fail("stale resume"))
