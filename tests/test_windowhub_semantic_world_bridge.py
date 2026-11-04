from app.agent.environment.environment_observation import EnvironmentObservation
from app.agent.environment.environment_state import EnvironmentState
from app.agent.perception.interaction_capability import InteractionCapability
from app.agent.perception.screen_element import ScreenElement
from app.agent.perception.screen_scene import ScreenScene
from app.agent.perception.windowhub_semantic_world import enrich_windowhub_scene
from app.agent.bridge.agent_task_v2_world_builder import AgentTaskV2WorldBuilder
from app.agent.runtime.computer_use_v2_action_session import ComputerUseV2ActionSession


def scene(title="Właściwości dokumentu", *elements, app="Okna.exe"):
    return ScreenScene(
        observation=EnvironmentObservation(
            state=EnvironmentState(active_application=app, active_window_title=title)
        ),
        elements=tuple(elements),
    )


def button(identifier="IDC_NEW", label="OknaWPF"):
    return ScreenElement(
        kind="button", label=label, x=20, y=30, width=32, height=23,
        interaction_capability=InteractionCapability.CLICKABLE,
        metadata={
            "source": "windowhub_ui_automation", "uia_control_type": "button",
            "automation_id": identifier, "uia_runtime_id": f"runtime-{identifier}",
            "uia_enabled": True, "uia_visible": True,
        },
    )


def test_native_add_label_is_explained_to_navimind_without_changing_executor_target():
    s = enrich_windowhub_scene(scene("Właściwości dokumentu", button()))
    e = s.elements[0]
    assert e.label == "OknaWPF"
    assert e.metadata["automation_id"] == "IDC_NEW"
    assert e.metadata["semantic_label"] == "Dodaj nowego klienta"
    cycle = ComputerUseV2ActionSession().prepare_cycle(
        s, task_id="teach-v2-test", goal="Utwórz nowego klienta",
        world_revision=1, observed_at="2026-11-04T10:00:00Z",
    )
    world = cycle.request_payload["world"]
    assert world["entities"][0]["label"] == "Dodaj nowego klienta"
    assert "IDC_NEW" not in str(cycle.request_payload)
    affordance = world["affordances"][0]
    assert "Dodaj nowego klienta" in affordance["description"]
    assert affordance["requires_confirmation"] is True
    action = cycle.request_payload["capabilities"]["actions"][0]
    assert action["requires_confirmation"] is True


def test_aliases_do_not_apply_to_other_apps_or_other_stages():
    other = scene("Właściwości dokumentu", button(), app="Code.exe")
    assert enrich_windowhub_scene(other) is other
    different_stage = scene("Zakładanie nowego klienta", button())
    assert enrich_windowhub_scene(different_stage) is different_stage


def test_click_target_remains_original_local_label():
    s = enrich_windowhub_scene(scene("Właściwości dokumentu", button()))
    snapshot = AgentTaskV2WorldBuilder().build(
        s, task_id="local-target", world_revision=2,
        observed_at="2026-11-04T10:00:00Z",
    )
    target = snapshot.reference_map.resolve(
        "ent_0001", task_id="local-target", world_revision=2,
    )
    assert target.label == "OknaWPF"
    assert target.metadata["automation_id"] == "IDC_NEW"
