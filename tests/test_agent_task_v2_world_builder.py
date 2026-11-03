import pytest

from app.agent.bridge.agent_task_contract_v2 import (
    validate_agent_task_v2_payload,
)
from app.agent.bridge.agent_task_v2_world_builder import (
    AgentTaskV2WorldBuilder,
)
from app.agent.environment.environment_observation import (
    EnvironmentObservation,
)
from app.agent.environment.environment_state import (
    EnvironmentState,
)
from app.agent.perception.interaction_capability import (
    InteractionCapability,
)
from app.agent.perception.screen_element import ScreenElement
from app.agent.perception.screen_scene import ScreenScene
from app.agent.perception.semantic_evidence import (
    EvidenceKind,
    EvidenceSource,
    SemanticEvidence,
)


def make_scene():
    label_evidence = SemanticEvidence(
        source=EvidenceSource.ACCESSIBILITY,
        kind=EvidenceKind.LABEL,
        value="Zamawiający",
        confidence=0.99,
        element_id="uia:[7,18708,63003992]",
    )
    bounds_evidence = SemanticEvidence(
        source=EvidenceSource.ACCESSIBILITY,
        kind=EvidenceKind.BOUNDS,
        value=(10, 20, 300, 40),
        confidence=0.99,
        element_id="uia:[7,18708,63003992]",
    )
    element = ScreenElement(
        kind="edit",
        label="Zamawiający",
        x=10,
        y=20,
        width=300,
        height=40,
        confidence=0.98,
        metadata={
            "tracked_object_id": "TO-SECRET-77",
            "uia_runtime_id": "[7,18708,63003992]",
            "automation_id": "IDC_ZAMAWIAJACY",
            "provider_element_id": "uia:private-provider-id",
            "current_value": "",
        },
        interaction_capability=InteractionCapability.CLICKABLE,
        evidence=(label_evidence, bounds_evidence),
    )
    return ScreenScene(
        observation=EnvironmentObservation(
            state=EnvironmentState(
                active_application="WindowHub",
                active_window_title="Nowa oferta",
                screen_width=1920,
                screen_height=1080,
            ),
            metadata={
                "window_handle": 1234,
                "screenshot": "private-screenshot-reference",
            },
        ),
        elements=(element,),
    )


def test_world_builder_projects_existing_scene_and_evidence():
    scene = make_scene()
    snapshot = AgentTaskV2WorldBuilder().build(
        scene,
        task_id="task-001",
        world_revision=7,
        observed_at="2026-11-02T06:00:00Z",
    )

    world = snapshot.payload
    assert world["revision"] == 7
    assert world["application"] == "WindowHub"
    assert world["window_title"] == "Nowa oferta"
    assert len(world["entities"]) == 1

    entity = world["entities"][0]
    assert entity["ref"] == "ent_0001"
    assert entity["type"] == "edit"
    assert entity["label"] == "Zamawiający"
    assert entity["state"]["interaction_capability"] == "clickable"
    assert entity["state"]["value_present"] is False
    assert entity["evidence_refs"] == ["ev_0001"]

    assert world["evidence"][0]["source"] == "accessibility"
    assert world["evidence"][0]["content"] == {
        "kind": "label",
        "value": "Zamawiający",
        "observed": True,
    }
    assert world["relationships"] == []
    assert [item["name"] for item in world["affordances"]] == [
        "click",
        "write_text",
    ]
    assert all(
        item["entity_ref"] == "ent_0001"
        for item in world["affordances"]
    )
    assert world["affordances"][1]["requires_confirmation"] is False


def test_world_builder_never_exposes_native_ids_coordinates_or_raw_values():
    snapshot = AgentTaskV2WorldBuilder().build(
        make_scene(),
        task_id="task-001",
        world_revision=7,
        observed_at="2026-11-02T06:00:00Z",
    )
    serialized = str(snapshot.payload)

    assert "TO-SECRET-77" not in serialized
    assert "IDC_ZAMAWIAJACY" not in serialized
    assert "uia:private-provider-id" not in serialized
    assert "18708" not in serialized
    assert "window_handle" not in serialized
    assert "screenshot" not in serialized
    assert "bounds" not in serialized
    assert "1920" not in serialized
    assert "1080" not in serialized


def test_reference_map_resolves_only_with_matching_task_and_revision():
    scene = make_scene()
    snapshot = AgentTaskV2WorldBuilder().build(
        scene,
        task_id="task-001",
        world_revision=7,
    )

    resolved = snapshot.reference_map.resolve(
        "ent_0001",
        task_id="task-001",
        world_revision=7,
    )
    assert resolved is scene.elements[0]

    try:
        snapshot.reference_map.resolve(
            "ent_0001",
            task_id="other-task",
            world_revision=7,
        )
    except ValueError as exc:
        assert "task_mismatch" in str(exc)
    else:
        raise AssertionError("Cross-task semantic reference was accepted.")

    try:
        snapshot.reference_map.resolve(
            "ent_0001",
            task_id="task-001",
            world_revision=8,
        )
    except ValueError as exc:
        assert "revision_mismatch" in str(exc)
    else:
        raise AssertionError("Stale semantic reference was accepted.")

    try:
        snapshot.reference_map.resolve(
            "ent_missing",
            task_id="task-001",
            world_revision=7,
        )
    except KeyError as exc:
        assert "unknown" in str(exc)
    else:
        raise AssertionError("Unknown semantic reference was accepted.")


def test_world_builder_handles_missing_scene_without_inventing_entities():
    snapshot = AgentTaskV2WorldBuilder().build(
        None,
        task_id="task-001",
        world_revision=0,
        observed_at="2026-11-02T06:00:00Z",
    )

    assert snapshot.payload["application"] is None
    assert snapshot.payload["window_title"] is None
    assert snapshot.payload["entities"] == []
    assert snapshot.payload["evidence"] == []
    assert snapshot.reference_map.refs == ()


def test_world_builder_bounds_entity_count():
    scene = make_scene()
    many_elements = tuple(
        ScreenElement(
            kind="button",
            label=f"Przycisk {index}",
            confidence=0.9,
        )
        for index in range(205)
    )
    large_scene = ScreenScene(
        observation=scene.observation,
        elements=many_elements,
    )

    snapshot = AgentTaskV2WorldBuilder().build(
        large_scene,
        task_id="task-001",
        world_revision=7,
    )

    assert len(snapshot.payload["entities"]) == 200
    limitation_evidence = snapshot.payload["evidence"][-1]
    assert limitation_evidence["content"] == {
        "kind": "projection_limitations",
        "omitted_entities": 5,
        "omitted_evidence": 0,
    }
    assert limitation_evidence["limitations"] == [
        "5 scene elements omitted by the v2 entity limit."
    ]
    assert len(snapshot.reference_map.refs) == 200



def test_built_world_snapshot_satisfies_the_v2_request_contract():
    snapshot = AgentTaskV2WorldBuilder().build(
        make_scene(),
        task_id="task-001",
        world_revision=7,
        observed_at="2026-11-02T06:00:00Z",
    )
    request = {
        "version": "2",
        "task_id": "task-001",
        "goal": "Understand the visible form.",
        "intent": "computer_use",
        "session_id": None,
        "task_state": {
            "cycle": 1,
            "max_cycles": 30,
            "reasoning_calls_remaining": 5,
        },
        "world": dict(snapshot.payload),
        "capabilities": {"observations": [], "actions": []},
        "knowledge": None,
        "experience": [],
        "constraints": {
            "max_observations_per_cycle": 1,
            "max_observation_items": 20,
            "max_evidence_bytes": 32_768,
            "semantic_only": True,
            "verify_each_action": True,
        },
        "metadata": {},
    }

    validate_agent_task_v2_payload(request)



def _scene_with_element(element):
    return ScreenScene(
        observation=EnvironmentObservation(
            state=EnvironmentState(
                active_application="WindowHub",
                active_window_title="Nowa oferta",
            )
        ),
        elements=(element,),
    )


def test_reference_map_resolves_unique_ref_for_exact_local_element():
    element = ScreenElement(kind="button", label="Nowa oferta")
    snapshot = AgentTaskV2WorldBuilder().build(
        _scene_with_element(element),
        task_id="reference-task",
        world_revision=8,
        observed_at="2026-11-02T09:00:00Z",
    )

    ref = snapshot.reference_map.ref_for(
        element,
        task_id="reference-task",
        world_revision=8,
    )

    assert ref == "ent_0001"
    assert snapshot.reference_map.resolve(
        ref,
        task_id="reference-task",
        world_revision=8,
    ) is element


def test_reference_map_rejects_wrong_task_or_revision():
    element = ScreenElement(kind="button", label="Nowa oferta")
    snapshot = AgentTaskV2WorldBuilder().build(
        _scene_with_element(element),
        task_id="reference-task",
        world_revision=8,
    )

    with pytest.raises(ValueError, match="task_mismatch"):
        snapshot.reference_map.ref_for(
            element,
            task_id="another-task",
            world_revision=8,
        )

    with pytest.raises(ValueError, match="revision_mismatch"):
        snapshot.reference_map.ref_for(
            element,
            task_id="reference-task",
            world_revision=9,
        )


def test_reference_map_rejects_element_mapped_to_multiple_refs():
    element = ScreenElement(kind="button", label="Nowa oferta")
    snapshot = AgentTaskV2WorldBuilder().build(
        ScreenScene(
            observation=EnvironmentObservation(
                state=EnvironmentState(
                    active_application="WindowHub",
                    active_window_title="Nowa oferta",
                )
            ),
            elements=(element, element),
        ),
        task_id="reference-task",
        world_revision=8,
    )

    with pytest.raises(ValueError, match="element_not_unique"):
        snapshot.reference_map.ref_for(
            element,
            task_id="reference-task",
            world_revision=8,
        )



def test_world_builder_marks_destructive_click_affordances_for_confirmation():
    element = ScreenElement(
        kind="button",
        label="Delete customer",
        interaction_capability=InteractionCapability.CLICKABLE,
    )
    snapshot = AgentTaskV2WorldBuilder().build(
        _scene_with_element(element),
        task_id="confirmation-task",
        world_revision=1,
    )

    affordance = snapshot.payload["affordances"][0]
    assert affordance["name"] == "click"
    assert affordance["requires_confirmation"] is True


def test_world_builder_does_not_publish_actions_for_non_interactive_controls():
    element = ScreenElement(
        kind="button",
        label="Disabled button",
        metadata={"uia_enabled": False},
        interaction_capability=InteractionCapability.CLICKABLE,
    )
    snapshot = AgentTaskV2WorldBuilder().build(
        _scene_with_element(element),
        task_id="disabled-task",
        world_revision=1,
    )

    assert snapshot.payload["affordances"] == []



def test_world_builder_exposes_root_window_role_without_native_owner_handle():
    window = ScreenElement(
        kind="application_window",
        label="Okna - OFR/4522- — Okna.exe",
        confidence=0.99,
        metadata={
            "source": "windows_desktop_window",
            "window_handle": 987654,
            "root_owner_handle": 987654,
            "is_root_window": True,
            "window_area": 1936 * 1168,
            "is_foreground": False,
            "is_minimized": False,
            "is_visible": True,
        },
        interaction_capability=InteractionCapability.UNKNOWN,
    )
    snapshot = AgentTaskV2WorldBuilder().build(
        _scene_with_element(window),
        task_id="root-window-task",
        world_revision=2,
        observed_at="2026-11-03T10:00:00Z",
    )

    entity = snapshot.payload["entities"][0]
    assert entity["state"]["is_root_window"] is True
    assert entity["state"]["window_area"] == 1936 * 1168
    assert "987654" not in str(snapshot.payload)
    assert "root_owner_handle" not in str(snapshot.payload)
    assert "window_handle" not in str(snapshot.payload)


@pytest.mark.parametrize(
    "button_label",
    (
        "Speichern",
        "Angebot erstellen",
        "Zapisz ofertę",
        "Create offer",
    ),
)
def test_world_builder_requires_confirmation_for_offer_commit_buttons(
    button_label,
):
    element = ScreenElement(
        kind="button",
        label=button_label,
        interaction_capability=InteractionCapability.CLICKABLE,
    )
    snapshot = AgentTaskV2WorldBuilder().build(
        _scene_with_element(element),
        task_id="offer-confirmation-task",
        world_revision=1,
    )

    affordance = snapshot.payload["affordances"][0]
    assert affordance["name"] == "click"
    assert affordance["requires_confirmation"] is True

