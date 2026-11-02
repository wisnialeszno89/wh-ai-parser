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
    assert world["affordances"] == []


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
