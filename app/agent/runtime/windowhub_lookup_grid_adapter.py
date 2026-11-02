"""WindowHub adapter for resolving the Client LookupEdit and its child grid.

The adapter bridges generic semantic target resolution with a fresh UIA
re-resolution. It exposes the customer grid only when the current ScreenScene
proves that PART_GridControl is structurally contained by IDC_ZAMAWIAJACY.
It never reads grid cells, headers, row text, or business-record values.
"""
from __future__ import annotations

from collections.abc import Callable

from app.agent.environment.environment_observation import (
    EnvironmentObservation,
)
from app.agent.perception.screen_element import ScreenElement
from app.agent.perception.screen_scene import ScreenScene
from app.agent.perception.semantic_target_query import (
    SemanticAncestorConstraint,
    SemanticTargetQuery,
)
from app.agent.perception.target_resolver import (
    TargetResolution,
    TargetResolver,
)
from app.agent.perception.windowhub_ui_automation_provider import (
    WindowHubUIAutomationProvider,
)


WINDOWHUB_CLIENT_LOOKUP_AUTOMATION_ID = "IDC_ZAMAWIAJACY"
WINDOWHUB_LOOKUP_GRID_AUTOMATION_ID = "PART_GridControl"


class WindowHubLookupGridAdapter:
    """Resolve the Client lookup grid semantically and re-find it for reading."""

    _CLIENT_GRID_QUERY = SemanticTargetQuery(
        role="table",
        automation_id=WINDOWHUB_LOOKUP_GRID_AUTOMATION_ID,
        within=SemanticAncestorConstraint(
            control_type="button",
            class_name="lookupedit",
            automation_id=WINDOWHUB_CLIENT_LOOKUP_AUTOMATION_ID,
        ),
        description="WindowHub Client Lookup grid",
    )

    def __init__(
        self,
        *,
        provider: WindowHubUIAutomationProvider,
        target_resolver: TargetResolver | None = None,
    ) -> None:
        if not callable(
            getattr(provider, "resolve_table_element", None)
        ):
            raise TypeError("windowhub_lookup_grid_provider_invalid")
        self._provider = provider
        self._target_resolver = target_resolver or TargetResolver()

    def resolve_scene_target(
        self,
        scene: ScreenScene,
    ) -> TargetResolution:
        """Return the unique current DataGrid contained by the Client LookupEdit."""
        return self._target_resolver.resolve(
            scene,
            self._CLIENT_GRID_QUERY,
        )

    def resolve_current_grid(
        self,
        target: ScreenElement,
        observation: EnvironmentObservation,
    ):
        """Return a fresh UIA wrapper after revalidating grid and lookup ancestry."""
        self._validate_scene_target(target)
        return self._provider.resolve_table_element(
            target,
            observation,
            required_ancestor_automation_ids=(
                WINDOWHUB_CLIENT_LOOKUP_AUTOMATION_ID,
            ),
            required_ancestor_properties={
                "control_type": "button",
                "class_name": "lookupedit",
                "automation_id": WINDOWHUB_CLIENT_LOOKUP_AUTOMATION_ID,
            },
        )

    def resolver_for_observation(
        self,
        observation: EnvironmentObservation,
    ) -> Callable[[ScreenElement], object]:
        """Build the callable expected by the read-only grid structure reader."""
        return lambda target: self.resolve_current_grid(
            target,
            observation,
        )

    def register_structure_capability(
        self,
        broker,
        observation: EnvironmentObservation,
        *,
        timeout_seconds: float = 2.0,
    ) -> str:
        """Register the grid-structure-only reader with a local v2 broker."""
        from app.agent.runtime.windowhub_uia_grid_structure_reader import (
            WindowHubUIAGridStructureReader,
            windowhub_grid_structure_capability_spec,
        )

        register = getattr(broker, "register", None)
        if not callable(register):
            raise TypeError("windowhub_lookup_grid_broker_invalid")

        reader = WindowHubUIAGridStructureReader(
            grid_resolver=self.resolver_for_observation(observation),
        )
        spec = windowhub_grid_structure_capability_spec(
            timeout_seconds=timeout_seconds,
        )
        register(spec, reader)
        return spec.name

    @classmethod
    def query(cls) -> SemanticTargetQuery:
        """Expose the immutable query for local skills and tests."""
        return cls._CLIENT_GRID_QUERY

    @classmethod
    def _validate_scene_target(cls, target: ScreenElement) -> None:
        metadata = target.metadata or {}
        if (
            target.kind != "table"
            or metadata.get("source") != "windowhub_ui_automation"
            or str(metadata.get("uia_control_type", "")).strip().casefold()
            not in {"datagrid", "table"}
            or not isinstance(metadata.get("automation_id"), str)
            or metadata["automation_id"].strip().casefold()
            != WINDOWHUB_LOOKUP_GRID_AUTOMATION_ID.casefold()
        ):
            raise ValueError("windowhub_client_grid_target_invalid")

        ancestry = metadata.get("uia_ancestor_structure")
        if not isinstance(ancestry, (tuple, list)):
            raise ValueError("windowhub_client_lookup_ancestry_missing")

        constraint = cls._CLIENT_GRID_QUERY.within
        if constraint is None or not any(
            constraint.matches(item)
            for item in ancestry
        ):
            raise ValueError("windowhub_client_grid_lookup_relationship_unverified")

        runtime_id = metadata.get("uia_runtime_id")
        if not isinstance(runtime_id, str) or not runtime_id.strip():
            raise ValueError("windowhub_client_grid_runtime_identity_missing")
