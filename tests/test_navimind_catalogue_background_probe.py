"""Independent local WH Okna HWND identity; PowerShell may own foreground."""
from types import SimpleNamespace as NS

from app.agent.runtime.navimind_catalogue_background_probe import (
    read_catalogue_window_without_focus,
)
from app.agent.runtime.navimind_catalogue_readiness import (
    inspect_catalogue_scene,
)
from app.agent.perception.screen_element import ScreenElement


def wizard(handle=55, title="Podstawowe parametry okna", app="Okna.exe"):
    return NS(
        handle=handle, title=title, application=app,
        rect=NS(left=0, top=0, width=800, height=600),
        root_owner_handle=handle,
        is_visible=True, is_minimized=False, is_foreground=False,
    )


def provider():
    class Fake:
        def perceive(self, observation):
            assert observation.metadata["window_handle"] == 55
            assert observation.state.active_application == "Okna.exe"
            return (ScreenElement(
                kind="combobox", label="Wybierz kolor profili",
                metadata={
                    "source": "windowhub_ui_automation",
                    "uia_visible": True, "uia_enabled": True,
                    "uia_runtime_id": "combo:1",
                    "automation_id": "1054",
                    "current_value": "BIAŁY",
                    "current_value_source": "selected_text",
                },
            ),)
    return Fake()


def test_background_wizard_scan_works_when_powershell_has_focus():
    scene, reason = read_catalogue_window_without_focus(
        inventory=[wizard()],
        provider=provider(),
        native_verifier=lambda hwnd, title: hwnd == 55,
    )
    assert reason == "native_catalogue_wizard_read_only"
    assert scene.observation.metadata["window_handle"] == 55
    audit = inspect_catalogue_scene(scene)
    assert audit.stage == "basic_parameters"
    assert any(
        x.field_name == "profile_color" and x.native_value_readable
        for x in audit.controls
    )


def test_no_wizard_or_multiple_candidates_are_fail_closed():
    for items, reason in (
        ([], "catalogue_wizard_not_found"),
        ([wizard(55), wizard(66)], "multiple_catalogue_wizards_ambiguous"),
        ([wizard(55, app="notepad.exe")], "catalogue_wizard_not_found"),
    ):
        result, actual = read_catalogue_window_without_focus(
            inventory=items, provider=provider(),
            native_verifier=lambda *_: True,
        )
        assert result is None and actual == reason


def test_stale_handle_is_rechecked_after_uia_traversal():
    calls = []
    def verify(hwnd, title):
        calls.append((hwnd, title))
        return len(calls) == 1
    result, reason = read_catalogue_window_without_focus(
        inventory=[wizard()],
        provider=provider(),
        native_verifier=verify,
    )
    assert result is None
    assert reason == "windowhub_native_process_changed_during_scan"
    assert len(calls) == 2


def test_injected_inventory_requires_explicit_win32_verifier():
    scene, reason = read_catalogue_window_without_focus(
        inventory=[wizard()], provider=provider(),
    )
    assert scene is None and reason == "injected_inventory_verifier_missing"


def test_bounded_catalogue_reader_does_not_scan_unlimited_mdi_tree():
    from app.agent.perception.windowhub_ui_automation_provider import (
        WindowHubUIAutomationProvider,
    )
    from app.agent.environment.environment_observation import (
        EnvironmentObservation,
    )
    from app.agent.environment.environment_state import EnvironmentState

    class Root:
        def window_text(self):
            return "Podstawowe parametry okna"
        def descendants(self, depth=None):
            assert depth == 5
            return tuple(range(5))
    class Desktop:
        def window(self, *, handle):
            assert handle == 55
            return NS(wrapper_object=lambda: Root())

    class Probe(WindowHubUIAutomationProvider):
        def _collect_label_candidates(self, *args, **kwargs):
            return ()
        def _to_screen_element(self, *, item, **kwargs):
            return ScreenElement(kind="edit", label=str(item))

    inspector = Probe(desktop_factory=lambda: Desktop())
    obs = EnvironmentObservation(
        state=EnvironmentState(
            active_application="Okna.exe",
            active_window_title="Podstawowe parametry okna",
        ), metadata={"window_handle": 55},
    )
    assert inspector.perceive_catalogue_bounded(obs, max_descendants=4) == ()
    assert len(inspector.perceive_catalogue_bounded(
        obs, max_descendants=5,
    )) == 5
