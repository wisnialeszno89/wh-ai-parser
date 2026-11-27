from dataclasses import replace

import pytest

from app.agent.environment.environment_observation import EnvironmentObservation
from app.agent.environment.environment_state import EnvironmentState
from app.agent.perception.screen_element import ScreenElement
from app.agent.perception.screen_scene import ScreenScene
from app.agent.runtime.navimind_position_ledger import PositionLedger, PositionManifest, SourcePosition
from app.agent.runtime.navimind_work_mission import WorkMission, WorkStage, plan_or_execute_windowhub_step
from app.agent.runtime.navimind_shared_control_host import VerifiedWorkflowScope
from app.agent.runtime.navimind_local_input_arbiter import InputDenied

DOCUMENT = "OFR/101"
POSITION = SourcePosition("S01-P001", 1, 1, "window", 1500, 1400, 1, None, "source", "Fenster")


def control(kind, label, aid, *, value=None, selected=None):
    return ScreenElement(
        kind, label, metadata={
            "source": "windows_ui_automation",
            "automation_id": aid,
            "uia_runtime_id": "uia:" + aid,
            "uia_control_type": kind,
            "uia_enabled": True,
            "uia_visible": True,
            "current_value": value,
            "current_value_source": "value",
            "uia_selected": selected,
        },
    )


NEXT = control("button", "Dalej >", "12324")


def wizard(title, *controls):
    return ScreenScene(EnvironmentObservation(
        EnvironmentState("Okna.exe", title), {"window_handle": 42},
    ), controls)


class LocalWizard:
    """Simulate only native observation and execution at the real mission boundary."""

    expected_offer = DOCUMENT

    def __init__(self, stage, before, after):
        self._workflow_scope = VerifiedWorkflowScope(
            document_key=DOCUMENT, revision=1, stage=stage,
            title=before.observation.state.active_window_title, hwnd=42,
        )
        self.before = before
        self.after = after
        self.actions = []

    def observe_scene(self):
        return self.after if self.actions else self.before

    def execute_one_verified_v2_action(self, loop, resolved, *, approved_persistent):
        assert loop is self
        assert approved_persistent is False
        self.actions.append(resolved.action)

    def note_verified_workflow_step(self, scene, *, revision):
        assert revision == 1
        return scene is self.after

    def reason(self, _payload):
        pytest.fail("Mapped geometry must not invoke the model")


def step(host):
    ledger = PositionLedger(PositionManifest((POSITION,)))
    mission = WorkMission("test", 1, 1, "Oferta dla Top Trans", DOCUMENT,
                          WorkStage.READY, position_ledger=ledger)
    return plan_or_execute_windowhub_step(
        mission=mission, loop=host, reasoner=host, host=host, execute=True,
    )


def test_live_mission_selects_window_then_advances_with_existing_exact_quantity():
    title = "Dodawanie nowej pozycji"
    unselected = control("radiobutton", "Okno", "1329", selected=False)
    selected = control("radiobutton", "Okno", "1329", selected=True)
    quantity = control("edit", "Ile sztuk", "1001", value="1")
    before = wizard(title, unselected, quantity, NEXT)
    after = wizard(title, selected, quantity, NEXT)
    host = LocalWizard("position", before, after)
    result = step(host)
    assert result.verified and host.actions[0].target.label == "Okno"

    host = LocalWizard("position", after, wizard("Wielkość okna"))
    result = step(host)
    assert result.verified and result.new_stage == "dimensions"
    assert [action.target.label for action in host.actions] == ["Dalej >"]


def test_live_mission_enters_width_then_height_and_reads_native_value_before_next():
    title = "Wielkość okna"
    width_before = control("edit", "Szerokość", "1000", value="1000")
    height_before = control("edit", "Wysokość", "1001", value="1200")
    width_after = replace(width_before, metadata={**width_before.metadata, "current_value": "1500"})
    height_after = replace(height_before, metadata={**height_before.metadata, "current_value": "1400"})
    before = wizard(title, width_before, height_before, NEXT)
    after_width = wizard(title, width_after, height_before, NEXT)
    after_height = wizard(title, width_after, height_after, NEXT)
    for original, updated, expected in (
        (before, after_width, "1500"),
        (after_width, after_height, "1400"),
    ):
        host = LocalWizard("dimensions", original, updated)
        result = step(host)
        assert result.verified and result.field_receipt.value == expected
        assert len(host.actions) == 1

    host = LocalWizard("dimensions", after_height, wizard("Podstawowe parametry okna"))
    result = step(host)
    assert result.verified and result.new_stage == "basic_parameters"


def test_ambiguous_width_is_a_precise_blocker_without_input():
    width = control("edit", "Szerokość", "1000", value="1500")
    scene = wizard("Wielkość okna", width, width)
    host = LocalWizard("dimensions", scene, scene)
    assert step(host).reason == "geometry_control_unverified:width_1"
    assert host.actions == []


def test_preinput_refusal_can_plan_again_while_uncertain_effect_requires_review():
    scene = wizard("Wielkość okna", control("edit", "Szerokość", "1000", value="1300"))
    host = LocalWizard("dimensions", scene, scene)

    def refuse(*_args, **_kwargs):
        raise InputDenied("preaction_uia_state_changed")

    host.execute_one_verified_v2_action = refuse
    result = step(host)
    assert (result.kind, result.reason) == ("paused", "local_preaction_scene_changed")

    def unverified(*_args, **_kwargs):
        raise RuntimeError("unverified_native_effect")

    host.execute_one_verified_v2_action = unverified
    assert step(host).kind == "review"
