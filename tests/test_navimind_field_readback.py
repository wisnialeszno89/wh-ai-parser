"""Exact native UIA field readback after one V2 write; entirely offline."""
from app.agent.environment.environment_observation import EnvironmentObservation
from app.agent.environment.environment_state import EnvironmentState
from app.agent.perception.screen_scene import ScreenScene
from app.agent.perception.screen_element import ScreenElement
from app.agent.runtime.navimind_field_readback import verify_written_field


def scene(*, title="Wielkość okna", value="1500", runtime_id="readback-7",
          app="Okna.exe", name="Szerokość", source="windowhub_ui_automation",
          current_value_source="get_value", extra=()):
    element = ScreenElement(
        kind="edit", label=name, metadata={
            "source": source,
            "automation_id": "1000",
            "uia_runtime_id": runtime_id,
            "uia_visible": True,
            "uia_enabled": True,
            "current_value": value,
            "current_value_source": current_value_source,
        },
    )
    return ScreenScene(
        observation=EnvironmentObservation(
            state=EnvironmentState(
                active_application=app, active_window_title=title,
            ),
        ), elements=(element, *extra),
    )


def check(s):
    return verify_written_field(
        s, field_name="width_1", expected_value="1500",
        expected_runtime_id="readback-7", expected_stage="dimensions",
    )


def test_exact_native_uia_value_is_independently_verified():
    assert check(scene()).verified


def test_model_result_cannot_substitute_actual_value():
    assert not check(scene(value="1400")).verified
    assert not check(scene(value=None)).verified
    assert not check(scene(current_value_source=None)).verified
    assert not check(scene(source="computer_vision")).verified


def test_wrong_app_wrong_stage_or_different_control_cannot_pass():
    assert not check(scene(app="notepad.exe")).verified
    assert not check(scene(title="Parametry szklenia")).verified
    assert not check(scene(runtime_id="different")).verified
    assert not check(scene(name="Wysokość")).verified


def test_duplicate_uia_fields_cannot_pass():
    duplicate = ScreenElement(
        kind="edit", label="Szerokość", metadata={
            "source": "windowhub_ui_automation",
            "automation_id": "1000", "uia_runtime_id": "other",
            "uia_visible": True, "uia_enabled": True,
            "current_value": "1500", "current_value_source": "get_value",
        },
    )
    assert not check(scene(extra=(duplicate,))).verified


def test_missing_provenance_or_bad_reference_fails_closed():
    assert not verify_written_field(
        scene(), field_name="width_1", expected_value="1500",
        expected_runtime_id="", expected_stage="dimensions",
    ).verified
    assert not verify_written_field(
        scene(), field_name="customer_name", expected_value="1500",
        expected_runtime_id="readback-7", expected_stage="dimensions",
    ).verified
