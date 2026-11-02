"""Local V2 observation session for the WindowHub Client Lookup/Grid.

This module prepares the existing provider-neutral V2 contract from the
current ScreenScene, binds one locally approved UI-structure capability, and
dispatches only validated V2 observe decisions to the read-only broker.

It does not call NaviMind over HTTP and does not execute V2 actions. The
existing V1 reasoner/runtime remains unchanged until a dedicated V2 reasoner
and action dispatcher are implemented.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Callable

from app.agent.bridge.agent_task_contract_v2 import (
    AgentTaskV2Contract,
    validate_agent_task_v2_response,
)
from app.agent.bridge.agent_task_v2_world_builder import (
    AgentTaskV2WorldBuilder,
    AgentTaskV2WorldSnapshot,
)
from app.agent.perception.screen_scene import ScreenScene
from app.agent.runtime.read_only_observation_broker import (
    ReadOnlyObservationBroker,
)
from app.agent.runtime.windowhub_lookup_grid_adapter import (
    WindowHubLookupGridAdapter,
)


@dataclass
class PreparedWindowHubV2ObservationCycle:
    """One revision-bound V2 request and its private local observation broker."""

    request_payload: Mapping[str, object]
    snapshot: AgentTaskV2WorldSnapshot
    broker: ReadOnlyObservationBroker
    task_id: str
    world_revision: int
    max_observation_items: int
    max_evidence_bytes: int
    lookup_grid_target_ref: str | None
    observation_capability: Mapping[str, object] | None
    _observation_consumed: bool = field(
        default=False,
        init=False,
        repr=False,
    )

    def execute_observation_decision(
        self,
        response: Mapping[str, object],
    ) -> Mapping[str, object]:
        """Validate and execute at most one observe decision from this cycle."""
        if self._observation_consumed:
            raise ValueError(
                "windowhub_v2_observation_decision_already_consumed"
            )

        validate_agent_task_v2_response(
            response,
            self.request_payload,
        )
        if response.get("decision") != "observe":
            raise ValueError(
                "windowhub_v2_session_expected_observe_decision"
            )

        request = response.get("observation_request")
        if not isinstance(request, Mapping):
            raise ValueError(
                "windowhub_v2_session_observation_request_invalid"
            )

        # Consume the decision before entering the provider. A failed or late
        # COM call requires a new observation cycle, not replay of this one.
        self._observation_consumed = True
        return self.broker.observe(
            request,
            task_id=self.task_id,
            world_revision=self.world_revision,
            max_observation_items=self.max_observation_items,
            max_evidence_bytes=self.max_evidence_bytes,
        )

    def revoke(self) -> None:
        """Drop all task-scoped capability bindings owned by this cycle."""
        self._observation_consumed = True
        self.broker.revoke_task(self.task_id)


class WindowHubV2ObservationSession:
    """Prepare and dispatch bounded V2 observations for a WindowHub scene."""

    def __init__(
        self,
        *,
        lookup_grid_adapter: WindowHubLookupGridAdapter,
        world_builder: AgentTaskV2WorldBuilder | None = None,
        broker_factory: Callable[[], ReadOnlyObservationBroker] | None = None,
    ) -> None:
        if not isinstance(lookup_grid_adapter, WindowHubLookupGridAdapter):
            raise TypeError("windowhub_v2_lookup_grid_adapter_invalid")
        self._lookup_grid_adapter = lookup_grid_adapter
        self._world_builder = world_builder or AgentTaskV2WorldBuilder()
        self._broker_factory = (
            broker_factory or ReadOnlyObservationBroker
        )

    def prepare_cycle(
        self,
        scene: ScreenScene,
        *,
        task_id: str,
        goal: str,
        intent: str = "computer_use",
        world_revision: int = 0,
        session_id: str | None = None,
        task_state: Mapping[str, object] | None = None,
        knowledge: Mapping[str, object] | None = None,
        experience: Sequence[Mapping[str, object]] = (),
        max_observation_items: int = 10,
        max_evidence_bytes: int = 2_048,
        observed_at: str | None = None,
    ) -> PreparedWindowHubV2ObservationCycle:
        """Create a validated model-facing cycle with local lookup-grid binding."""
        if isinstance(max_observation_items, bool) or not 1 <= max_observation_items <= 10:
            raise ValueError("windowhub_v2_observation_item_budget_invalid")
        if (
            isinstance(max_evidence_bytes, bool)
            or not 1_024 <= max_evidence_bytes <= 32_768
        ):
            raise ValueError("windowhub_v2_evidence_byte_budget_invalid")

        observation = scene.observation
        if observation is None:
            raise ValueError("windowhub_v2_scene_observation_required")

        snapshot = self._world_builder.build(
            scene,
            task_id=task_id,
            world_revision=world_revision,
            observed_at=observed_at,
        )

        broker = self._broker_factory()
        if not isinstance(broker, ReadOnlyObservationBroker):
            raise TypeError("windowhub_v2_broker_factory_invalid")

        observations: list[Mapping[str, object]] = []
        target_ref: str | None = None
        capability_descriptor: Mapping[str, object] | None = None

        resolution = self._lookup_grid_adapter.resolve_scene_target(scene)
        if resolution.resolved and resolution.element is not None:
            target_ref = snapshot.reference_map.ref_for(
                resolution.element,
                task_id=task_id,
                world_revision=world_revision,
            )
            capability_name = (
                self._lookup_grid_adapter.register_structure_capability(
                    broker,
                    observation,
                    max_items=max_observation_items,
                    max_result_bytes=max_evidence_bytes,
                )
            )
            capability_descriptor = broker.bind(
                snapshot,
                capability_name=capability_name,
                target_ref=target_ref,
            )
            observations.append(capability_descriptor)

        resolved_task_state = dict(
            task_state
            if task_state is not None
            else {
                "cycle": 0,
                "max_cycles": 30,
                "reasoning_calls_remaining": 1,
            }
        )

        contract = AgentTaskV2Contract(
            task_id=task_id,
            goal=goal,
            intent=intent,
            session_id=session_id,
            task_state=resolved_task_state,
            world=snapshot.payload,
            capabilities={
                "observations": observations,
                "actions": [],
            },
            knowledge=knowledge,
            experience=tuple(dict(item) for item in experience),
            constraints={
                "max_observations_per_cycle": 1,
                "max_observation_items": max_observation_items,
                "max_evidence_bytes": max_evidence_bytes,
                "semantic_only": True,
                "verify_each_action": True,
            },
        )
        request_payload = contract.to_payload()

        return PreparedWindowHubV2ObservationCycle(
            request_payload=request_payload,
            snapshot=snapshot,
            broker=broker,
            task_id=task_id,
            world_revision=world_revision,
            max_observation_items=max_observation_items,
            max_evidence_bytes=max_evidence_bytes,
            lookup_grid_target_ref=target_ref,
            observation_capability=capability_descriptor,
        )
