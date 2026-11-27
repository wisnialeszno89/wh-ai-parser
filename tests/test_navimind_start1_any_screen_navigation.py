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


def test_foreground_okna_root_disambiguates_only_known_frames():
    from types import SimpleNamespace
    from app.agent.runtime.windowhub_window_activation import select_start1_frame

    def frame(hwnd):
        return SimpleNamespace(handle=hwnd, application="Okna.exe", title="Okna - OFR/10",
                               is_visible=True, is_minimized=False)

    windows = [frame(10), frame(20)]
    api = SimpleNamespace(owner=lambda _: 0)
    active = SimpleNamespace(handle=20, active_application="Okna.exe", root_owner_handle=20)
    assert select_start1_frame(windows, active, api)[0] is windows[1]
    active.active_application = "python.exe"
    assert select_start1_frame(windows, active, api) == (None, "start1_main_frame_not_unique")
    active.active_application = "Okna.exe"
    active.root_owner_handle = 10
    assert select_start1_frame(windows, active, api) == (None, "start1_owned_dialog_active")
