"""Regression: fresh draft always returns to Start1 before creating an offer."""
from app.agent.runtime.windowhub_window_activation import unique_start1_navigation_candidate


def control(*, name="Start1", kind="button", enabled=True, visible=True,
            automation_id="ID_START1", runtime_id="1-2-3"):
    return dict(name=name, kind=kind, enabled=enabled, visible=visible,
                automation_id=automation_id, runtime_id=runtime_id)


def test_unique_named_start1_button_or_tab_is_eligible():
    assert unique_start1_navigation_candidate([control()]) == control()
    assert unique_start1_navigation_candidate(
        [control(kind="tabitem")]
    ) == control(kind="tabitem")


def test_reject_ambiguous_or_unidentified_start1_icons():
    assert unique_start1_navigation_candidate([control(), control()]) is None
    assert unique_start1_navigation_candidate(
        [control(name="Start2")]
    ) is None
    assert unique_start1_navigation_candidate(
        [control(automation_id="")]
    ) is None
    assert unique_start1_navigation_candidate(
        [control(runtime_id=None)]
    ) is None
    assert unique_start1_navigation_candidate(
        [control(visible=False)]
    ) is None
    assert unique_start1_navigation_candidate(
        [control(enabled=False)]
    ) is None


def test_ignore_other_open_offer_buttons():
    assert unique_start1_navigation_candidate([
        control(name="Dodaj"),
        control(name="Zapisz"),
        control(name="Start1"),
    ]) == control(name="Start1")


def test_draft_planner_returns_to_start1_before_order_or_existing_offer_work():
    import inspect
    from app.agent.runtime.navimind_work_mission import plan_or_execute_windowhub_step
    code = inspect.getsource(plan_or_execute_windowhub_step)
    # Regression guard: alternate stages are first handled as focus-only
    # Start1 navigation; never click a control in the unrelated active offer.
    marker = 'stage != "start"'
    assert marker in code
    assert code.index(marker) < code.index('if stage == "order_document"')
    assert 'draft_start1_not_verified_after_activation' in code
