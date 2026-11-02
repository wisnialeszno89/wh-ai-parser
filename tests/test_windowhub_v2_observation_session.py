from types import SimpleNamespace

import pytest

from app.agent.bridge.agent_task_contract_v2 import (
    validate_agent_task_v2_payload,
)
from app.agent.environment.environment_observation import EnvironmentObservation
from app.agent.environment.environment_state import EnvironmentState
from app.agent.perception.windowhub_ui_automation_provider import (
    WindowHubUIAutomationProvider,
)
from app.agent.perception.screen_scene import ScreenScene
from app.agent.runtime.windowhub_lookup_grid_adapter import (
    WINDOWHUB_CLIENT_LOOKUP_AUTOMATION_ID,
    WINDOWHUB_LOOKUP_GRID_AUTOMATION_ID,
    WindowHubLookupGridAdapter,
)
from app.agent.runtime.windowhub_v2_observation_session import (
    WindowHubV2ObservationSession,
)


class FakeUIAItem:
    def __init__(
        self,
        *,
        name="",
        control_type="Custom",
        class_name="",
        automation_id="",
        runtime_id=(1, 2, 3),
        enabled=True,
        visible=True,
        parent=None,
    ):
        self.element_info = SimpleNamespace(
            name=name,
            control_type=control_type,
            class_name=class_name,
            automation_id=automation_id,
            runtime_id=runtime_id,
            enabled=enabled,
            visible=visible,
            rich_text=None,
        )
        self._parent = parent
        self._rectangle = SimpleNamespace(
            left=100,
            top=200,
            width=lambda: 420,
            height=lambda: 260,
        )

    def parent(self):
        return self._parent

    def rectangle(self):
        return self._rectangle


class FakeGridPattern:
    CurrentRowCount = 23
    CurrentColumnCount = 5

    def __init__(self):
        self.cell_reads = 0

    def GetItem(self, _row, _column):
        self.cell_reads += 1
        raise AssertionError("V2 structural observation must not read cells")


class FakeUIAWindow:
    def __init__(self, items, title="Okna - WindowHub"):
        self._items = tuple(items)
        self._title = title

    def window_text(self):
        return self._title

    def descendants(self):
        return self._items


class FakeDesktop:
    def __init__(self, window):
        self._window = window

    def get_active(self):
        return self._window


def make_observation():
    return EnvironmentObservation(
        state=EnvironmentState(
            active_application="WindowHub",
            active_window_title="Okna - WindowHub",
        ),
        metadata={
            "window_rect": SimpleNamespace(
                left=0,
                top=0,
                width=1440,
                height=900,
            )
        },
    )


def make_provider(*, grid_present=True, client_parent=True):
    lookup = FakeUIAItem(
        name="Zamawiający",
        control_type="Button",
        class_name="lookupedit",
        automation_id=WINDOWHUB_CLIENT_LOOKUP_AUTOMATION_ID,
        runtime_id=(4, 10, 20),
    )
    items = [lookup]
    grid = None
    if grid_present:
        container_parent = lookup if client_parent else FakeUIAItem(
            name="",
            control_type="Pane",
            class_name="documentview",
            automation_id="IDC_DOKUMENT",
            runtime_id=(4, 10, 21),
        )
        container = FakeUIAItem(
            name="",
            control_type="Custom",
            class_name="popupcontent",
            runtime_id=(4, 10, 22),
            parent=container_parent,
        )
        grid = FakeUIAItem(
            name="",
            control_type="DataGrid",
            class_name="",
            automation_id=WINDOWHUB_LOOKUP_GRID_AUTOMATION_ID,
            runtime_id=(7, 18708, 63003992),
            parent=container,
        )
        grid.iface_grid = FakeGridPattern()
        grid.iface_table = object()
        items.extend((container, grid))

    window = FakeUIAWindow(items)
    desktop = FakeDesktop(window)
    return WindowHubUIAutomationProvider(
        desktop_factory=lambda: desktop,
    ), grid


def make_session(*, grid_present=True, client_parent=True):
    provider, grid = make_provider(
        grid_present=grid_present,
        client_parent=client_parent,
    )
    adapter = WindowHubLookupGridAdapter(provider=provider)
    session = WindowHubV2ObservationSession(
        lookup_grid_adapter=adapter,
    )
    observation = make_observation()
    scene = ScreenScene(
        observation=observation,
        elements=provider.perceive(observation),
    )
    return session, scene, grid


def prepare(session, scene, **kwargs):
    return session.prepare_cycle(
        scene,
        task_id="task-windowhub-v2",
        goal="Inspect the Client lookup grid structure.",
        intent="computer_use",
        world_revision=7,
        session_id="session-windowhub-v2",
        observed_at="2026-11-02T10:00:00Z",
        **kwargs,
    )


def make_observe_response(prepared, *, fields=None):
    descriptor = prepared.observation_capability
    assert descriptor is not None
    return {
        "version": "2",
        "task_id": prepared.task_id,
        "decision": "observe",
        "rationale": "The grid structure is needed for the next step.",
        "confidence": 0.97,
        "observation_request": {
            "capability_id": descriptor["id"],
            "target_ref": descriptor["target_ref"],
            "parameters": {
                "fields": fields or [
                    "row_count",
                    "column_count",
                    "grid_pattern_available",
                ]
            },
            "based_on_world_revision": prepared.world_revision,
        },
        "action": None,
        "completion": None,
        "requires_manual_review": False,
    }


def test_v2_session_builds_valid_contract_and_binds_only_client_grid():
    session, scene, _grid = make_session()
    prepared = prepare(session, scene)

    validate_agent_task_v2_payload(prepared.request_payload)

    observations = prepared.request_payload["capabilities"]["observations"]
    assert len(observations) == 1
    assert observations[0]["input_contract"] == "entity_inspection_v1"
    assert observations[0]["data_classification"] == "ui_structure"
    assert observations[0]["read_only"] is True
    assert prepared.lookup_grid_target_ref == observations[0]["target_ref"]
    assert prepared.lookup_grid_target_ref.startswith("ent_")

    world_entity_refs = {
        item["ref"]
        for item in prepared.request_payload["world"]["entities"]
    }
    assert prepared.lookup_grid_target_ref in world_entity_refs

    # Provider-native IDs stay inside the local reference map, not the payload.
    serialized = str(prepared.request_payload).casefold()
    assert "automation_id" not in serialized
    assert "uia_runtime_id" not in serialized
    assert WINDOWHUB_CLIENT_LOOKUP_AUTOMATION_ID.casefold() not in serialized
    assert WINDOWHUB_LOOKUP_GRID_AUTOMATION_ID.casefold() not in serialized


def test_v2_session_executes_valid_observe_response_through_local_broker():
    session, scene, grid = make_session()
    prepared = prepare(session, scene)

    evidence = prepared.execute_observation_decision(
        make_observe_response(prepared)
    )

    assert evidence["source"] == "uia_grid_structure"
    assert evidence["world_revision"] == 7
    assert evidence["content"] == {
        "fields": {
            "row_count": 23,
            "column_count": 5,
            "grid_pattern_available": True,
        }
    }
    assert grid.iface_grid.cell_reads == 0


def test_v2_session_rejects_unexposed_capability_before_observation():
    session, scene, grid = make_session()
    prepared = prepare(session, scene)
    response = make_observe_response(prepared)
    response["observation_request"]["capability_id"] = "obs_unexposed"

    with pytest.raises(ValueError, match="capability_not_exposed"):
        prepared.execute_observation_decision(response)

    assert grid.iface_grid.cell_reads == 0


def test_v2_session_does_not_expose_lookup_capability_without_matching_grid():
    session, scene, _grid = make_session(
        grid_present=True,
        client_parent=False,
    )
    prepared = prepare(session, scene)

    validate_agent_task_v2_payload(prepared.request_payload)

    assert prepared.lookup_grid_target_ref is None
    assert prepared.observation_capability is None
    assert prepared.request_payload["capabilities"]["observations"] == []


def test_v2_session_can_prepare_cycle_when_lookup_grid_is_not_visible():
    session, scene, _grid = make_session(grid_present=False)
    prepared = prepare(session, scene)

    validate_agent_task_v2_payload(prepared.request_payload)

    assert prepared.lookup_grid_target_ref is None
    assert prepared.request_payload["capabilities"]["observations"] == []


def test_v2_session_rejects_non_observe_decisions_in_observation_dispatch():
    session, scene, grid = make_session()
    prepared = prepare(session, scene)
    response = make_observe_response(prepared)
    response["decision"] = "done"
    response["observation_request"] = None
    response["completion"] = {"evidence_refs": ["ev_0001"]}

    with pytest.raises(ValueError, match="expected_observe_decision"):
        prepared.execute_observation_decision(response)

    assert grid.iface_grid.cell_reads == 0


def test_v2_session_revokes_task_bindings_after_cycle():
    session, scene, grid = make_session()
    prepared = prepare(session, scene)
    response = make_observe_response(prepared)
    request = response["observation_request"]

    prepared.revoke()

    from app.agent.runtime.read_only_observation_broker import ObservationRejected

    with pytest.raises(ObservationRejected, match="capability_not_exposed"):
        prepared.broker.observe(
            request,
            task_id=prepared.task_id,
            world_revision=prepared.world_revision,
            max_observation_items=prepared.max_observation_items,
            max_evidence_bytes=prepared.max_evidence_bytes,
        )

    assert grid.iface_grid.cell_reads == 0
