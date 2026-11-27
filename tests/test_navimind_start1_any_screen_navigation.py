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
                               is_visible=True, is_minimized=False, root_owner_handle=hwnd)

    windows = [frame(10), frame(20)]
    api = SimpleNamespace(
        owner=lambda _: 0, enabled=lambda _: True, mdi_hosts=lambda _: (), pid=lambda _: 100,
    )
    active = SimpleNamespace(handle=20, active_application="Okna.exe", root_owner_handle=20)
    assert select_start1_frame(windows, active, api)[0] is windows[1]
    active.active_application = "python.exe"
    assert select_start1_frame(windows, active, api) == (None, "start1_main_frame_not_unique")
    active.active_application = "Okna.exe"
    active.root_owner_handle = 10
    assert select_start1_frame(windows, active, api) == (None, "start1_owned_dialog_active")



class NativeWindowHub:
    """WindowHub with one native Start1 child and another unrelated top-level window."""

    def __init__(self):
        self.active = 40
        self.foreground_handle = 90
        self.requests = []
        self.allow_activation = True

    def owner(self, hwnd):
        return 0

    def enabled(self, hwnd):
        return True

    def mdi_hosts(self, hwnd):
        return (30,) if hwnd == 10 else ()

    def pid(self, hwnd):
        return 100 if hwnd in {10, 20, 30, 40, 50} else 0

    def parent(self, hwnd, kind):
        return {(30, 2): 10, (40, 1): 30, (50, 1): 30}.get((hwnd, kind))

    def descendants(self, host):
        return (40, 50) if host == 30 else ()

    def title(self, hwnd):
        return {
            10: "Okna - Start1" if self.active == 50 else "Okna",
            40: "OFR/101",
            50: "Start1",
        }.get(hwnd, "")

    def focus(self, hwnd):
        self.foreground_handle = hwnd
        return True

    def foreground(self):
        return self.foreground_handle

    def active_child(self, host):
        return self.active

    def activate_child(self, host, child):
        self.requests.append((host, child))
        if self.allow_activation:
            self.active = child
        return self.allow_activation


def window(hwnd, title, *, minimized=False):
    from types import SimpleNamespace

    return SimpleNamespace(
        application="Okna.exe", title=title, handle=hwnd, root_owner_handle=hwnd,
        is_visible=True, is_minimized=minimized,
    )


def test_resolve_start1_by_native_child_when_panel_is_foreground():
    from types import SimpleNamespace
    from app.agent.runtime.windowhub_window_activation import select_start1_frame

    actual = window(10, "Okna", minimized=True)
    unrelated = window(20, "Okna - OFR/808")
    foreground = SimpleNamespace(handle=90, active_application="python.exe", root_owner_handle=90)
    api = NativeWindowHub()

    frame, reason = select_start1_frame((unrelated, actual), foreground, api)
    assert (frame, reason) == (actual, "start1_verified_mdi_root")
    assert api.requests == []


def test_activate_start1_changes_only_the_proven_child_and_checks_result():
    from app.agent.runtime.windowhub_window_activation import _activate_native_start1

    api = NativeWindowHub()
    result = _activate_native_start1(
        window(10, "Okna"), api, focus=api.focus, still_current=lambda: True, wait_seconds=0,
    )
    assert result == (True, "start1_native_workspace_verified")
    assert api.requests == [(30, 50)]


def test_uncertain_native_start1_activation_does_not_fall_through_to_uia():
    from app.agent.runtime.windowhub_window_activation import _activate_native_start1

    api = NativeWindowHub()
    api.allow_activation = False
    result = _activate_native_start1(
        window(10, "Okna"), api, focus=api.focus, still_current=lambda: True, wait_seconds=0,
    )
    assert result == (False, "start1_mdi_activation_effect_uncertain")
    assert api.requests == [(30, 50)]


def test_cancelled_start1_navigation_does_not_select_another_child():
    from app.agent.runtime.windowhub_window_activation import _activate_native_start1

    api = NativeWindowHub()
    result = _activate_native_start1(
        window(10, "Okna"), api, focus=api.focus, still_current=lambda: False, wait_seconds=0,
    )
    assert result == (False, "start1_navigation_cancelled")
    assert api.requests == []
    assert api.foreground() == 90


def test_disabled_frame_is_not_activated_behind_a_modal_form():
    from types import SimpleNamespace
    from app.agent.runtime.windowhub_window_activation import select_start1_frame

    foreground = SimpleNamespace(handle=90, active_application="python.exe", root_owner_handle=90)
    api = NativeWindowHub()
    api.enabled = lambda hwnd: False

    assert select_start1_frame((window(10, "Okna - Start1"),), foreground, api) == (
        None, "start1_main_frame_disabled",
    )
    assert api.requests == []


def test_already_active_start1_does_not_dispatch_a_second_navigation():
    from app.agent.runtime.windowhub_window_activation import _activate_native_start1

    api = NativeWindowHub()
    api.active = 50
    result = _activate_native_start1(
        window(10, "Okna - Start1"), api, focus=api.focus,
        still_current=lambda: True, wait_seconds=0,
    )
    assert result == (True, "start1_native_workspace_verified")
    assert api.requests == []
