"""Build and locally resolve least-privilege NaviMind V2 computer-use actions."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Callable

from app.agent.agent_action import AgentAction
from app.agent.bridge.agent_task_contract_v2 import (
    AgentTaskV2Contract,
    validate_agent_task_v2_response,
)
from app.agent.bridge.agent_task_v2_world_builder import (
    AgentTaskV2WorldBuilder,
    AgentTaskV2WorldSnapshot,
)
from app.agent.perception.interaction_capability import InteractionCapability
from app.agent.perception.screen_element import ScreenElement
from app.agent.perception.screen_scene import ScreenScene
from app.agent.perception.target_resolver import TargetResolver
from app.runtime.execution.keyboard.keyboard_input_policy import (
    SAFE_KEY_SEQUENCES,
    normalize_keyboard_sequence,
)


MAX_V2_ACTION_CAPABILITIES = 64
MAX_DESKTOP_WINDOW_ACTION_CAPABILITIES = 8
_UIA_SOURCES = frozenset(
    {
        "windows_ui_automation",
        "windowhub_ui_automation",
    }
)


@dataclass(frozen=True)
class _LocalActionBinding:
    """Private action binding; never serialized to NaviMind."""

    action_name: str
    target_ref: str | None
    semantic_action: str
    requires_confirmation: bool
    value: str | None = None


@dataclass(frozen=True)
class ResolvedComputerUseV2Action:
    """A validated semantic action plus its required postcondition."""

    action: AgentAction
    target_ref: str | None
    expected_postcondition: Mapping[str, object]


@dataclass
class PreparedComputerUseV2Cycle:
    """One revision-scoped V2 request and its private local action map."""

    request_payload: Mapping[str, object]
    snapshot: AgentTaskV2WorldSnapshot
    scene: ScreenScene
    task_id: str
    world_revision: int
    _action_bindings: Mapping[str, _LocalActionBinding] = field(
        repr=False,
    )
    _decision_consumed: bool = field(
        default=False,
        init=False,
        repr=False,
    )

    def resolve_action_decision(
        self,
        response: Mapping[str, object],
    ) -> ResolvedComputerUseV2Action:
        """Validate one model decision and resolve it to a local semantic target."""
        if self._decision_consumed:
            raise ValueError("computer_use_v2_decision_already_consumed")

        validate_agent_task_v2_response(
            response,
            self.request_payload,
        )
        if response.get("decision") != "act":
            raise ValueError("computer_use_v2_expected_act_decision")

        raw_action = response.get("action")
        if not isinstance(raw_action, Mapping):
            raise ValueError("computer_use_v2_action_invalid")

        capability_name = raw_action.get("name")
        binding = (
            self._action_bindings.get(capability_name)
            if isinstance(capability_name, str)
            else None
        )
        if binding is None:
            raise ValueError("computer_use_v2_action_not_locally_bound")

        target_ref = raw_action.get("target_ref")
        if target_ref != binding.target_ref:
            raise ValueError("computer_use_v2_action_target_mismatch")

        value = raw_action.get("value")
        label: str | None = None

        window_handle: int | None = None
        element: ScreenElement | None = None

        if binding.semantic_action == "press_key":
            if binding.target_ref is not None or value not in (None, ""):
                raise ValueError("computer_use_v2_keyboard_action_payload_invalid")
            if not isinstance(binding.value, str):
                raise ValueError("computer_use_v2_keyboard_binding_invalid")
            normalize_keyboard_sequence(binding.value)
        else:
            if not isinstance(binding.target_ref, str):
                raise ValueError("computer_use_v2_target_binding_invalid")
            element = self.snapshot.reference_map.resolve(
                binding.target_ref,
                task_id=self.task_id,
                world_revision=self.world_revision,
            )
            if not self._is_unique_current_target(element):
                raise ValueError("computer_use_v2_target_no_longer_unique")

            label = element.label.strip() if isinstance(element.label, str) else ""
            if not label:
                raise ValueError("computer_use_v2_target_label_missing")

            if binding.semantic_action == "write_text":
                if not isinstance(value, str) or not value:
                    raise ValueError("computer_use_v2_write_text_value_missing")
            elif binding.semantic_action == "activate_window":
                if value not in (None, ""):
                    raise ValueError("computer_use_v2_window_action_payload_invalid")
                metadata = element.metadata or {}
                candidate_handle = metadata.get("window_handle")
                if (
                    metadata.get("source") != "windows_desktop_window"
                    or isinstance(candidate_handle, bool)
                    or not isinstance(candidate_handle, int)
                    or candidate_handle <= 0
                    or metadata.get("is_foreground") is not False
                    or not isinstance(binding.value, str)
                    or binding.value != str(candidate_handle)
                ):
                    raise ValueError("computer_use_v2_window_binding_invalid")
                window_handle = candidate_handle
            elif value not in (None, ""):
                raise ValueError("computer_use_v2_click_value_not_supported")

        requires_confirmation = raw_action.get("requires_confirmation")
        if not isinstance(requires_confirmation, bool):
            raise ValueError("computer_use_v2_confirmation_flag_invalid")
        if binding.requires_confirmation and not requires_confirmation:
            raise ValueError("computer_use_v2_confirmation_downgraded")

        expected_postcondition = raw_action.get("expected_postcondition")
        if not isinstance(expected_postcondition, Mapping):
            raise ValueError("computer_use_v2_postcondition_invalid")

        if binding.semantic_action == "press_key":
            self._validate_keyboard_postcondition(
                binding.value,
                expected_postcondition,
            )
            canonical_name = "press_key"
            description = (
                f"Press the allowlisted '{binding.value}' keyboard sequence "
                "on the active desktop window."
            )
            action_target = None
            action_value = binding.value
        elif binding.semantic_action == "write_text":
            canonical_name = "write_text"
            description = f"Enter the requested text in '{label}'."
            action_target = label
            action_value = value
        elif binding.semantic_action == "activate_window":
            self._validate_window_postcondition(expected_postcondition)
            canonical_name = "activate_window"
            description = f"Activate the open desktop window '{label}'."
            action_target = label
            action_value = str(window_handle)
        else:
            canonical_name = "click_screen_element"
            description = f"Click the visible control '{label}'."
            action_target = label
            action_value = None

        action = AgentAction(
            name=canonical_name,
            description=description,
            requires_confirmation=requires_confirmation,
            target=action_target,
            value=action_value,
            requires_environment_observation=True,
        )

        # A response is single-use. The next action must be based on a new
        # world revision and a fresh observation, never on a stale target map.
        self._decision_consumed = True
        return ResolvedComputerUseV2Action(
            action=action,
            target_ref=binding.target_ref,
            expected_postcondition=dict(expected_postcondition),
        )


    @staticmethod
    def _validate_window_postcondition(
        postcondition: Mapping[str, object],
    ) -> None:
        if postcondition.get("kind") != "scene_changed":
            raise ValueError(
                "computer_use_v2_window_requires_scene_change_postcondition"
            )

    @staticmethod
    def _validate_keyboard_postcondition(
        sequence: str | None,
        postcondition: Mapping[str, object],
    ) -> None:
        if not isinstance(sequence, str):
            raise ValueError("computer_use_v2_keyboard_sequence_missing")
        normalize_keyboard_sequence(sequence)

        kind = postcondition.get("kind")
        if sequence in {"tab", "shift+tab"}:
            if (
                kind != "entity_state_equals"
                or postcondition.get("state") != "uia_focused"
                or postcondition.get("expected_value") is not True
                or not isinstance(postcondition.get("target_ref"), str)
            ):
                raise ValueError(
                    "computer_use_v2_tab_requires_verified_focus_postcondition"
                )
            return

        if kind != "scene_changed":
            raise ValueError(
                "computer_use_v2_keyboard_requires_scene_change_postcondition"
            )

    def _is_unique_current_target(self, element: ScreenElement) -> bool:
        label = element.label
        if not isinstance(label, str) or not label.strip():
            return False
        resolution = TargetResolver().resolve(self.scene, label)
        return resolution.resolved and resolution.element is element


class ComputerUseV2ActionSession:
    """Prepare provider-neutral world requests with locally approved actions."""

    def __init__(
        self,
        *,
        world_builder: AgentTaskV2WorldBuilder | None = None,
        target_resolver_factory: Callable[[], TargetResolver] | None = None,
    ) -> None:
        self._world_builder = world_builder or AgentTaskV2WorldBuilder()
        self._target_resolver_factory = (
            target_resolver_factory or TargetResolver
        )

    def prepare_cycle(
        self,
        scene: ScreenScene,
        *,
        task_id: str,
        goal: str,
        world_revision: int,
        session_id: str | None = None,
        cycle: int = 0,
        max_cycles: int = 30,
        knowledge: Mapping[str, object] | None = None,
        experience: Sequence[Mapping[str, object]] = (),
        max_observation_items: int = 10,
        max_evidence_bytes: int = 2_048,
        observed_at: str | None = None,
    ) -> PreparedComputerUseV2Cycle:
        if isinstance(cycle, bool) or cycle < 0:
            raise ValueError("computer_use_v2_cycle_invalid")
        if isinstance(max_cycles, bool) or not 1 <= max_cycles <= 1_000:
            raise ValueError("computer_use_v2_max_cycles_invalid")
        if cycle > max_cycles:
            raise ValueError("computer_use_v2_cycle_exceeds_max")
        if not 1 <= max_observation_items <= 10:
            raise ValueError("computer_use_v2_observation_budget_invalid")
        if not 1_024 <= max_evidence_bytes <= 32_768:
            raise ValueError("computer_use_v2_evidence_budget_invalid")

        snapshot = self._world_builder.build(
            scene,
            task_id=task_id,
            world_revision=world_revision,
            observed_at=observed_at,
        )
        action_capabilities, action_bindings = self._build_action_capabilities(
            scene,
            snapshot,
            task_id=task_id,
            world_revision=world_revision,
        )

        contract = AgentTaskV2Contract(
            task_id=task_id,
            goal=goal,
            intent="computer_use",
            session_id=session_id,
            task_state={
                "cycle": cycle,
                "max_cycles": max_cycles,
                "reasoning_calls_remaining": 1,
            },
            world=snapshot.payload,
            capabilities={
                "observations": [],
                "actions": action_capabilities,
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
            metadata={},
        )
        request_payload = contract.to_payload()

        return PreparedComputerUseV2Cycle(
            request_payload=request_payload,
            snapshot=snapshot,
            scene=scene,
            task_id=task_id,
            world_revision=world_revision,
            _action_bindings=action_bindings,
        )

    def _build_action_capabilities(
        self,
        scene: ScreenScene,
        snapshot: AgentTaskV2WorldSnapshot,
        *,
        task_id: str,
        world_revision: int,
    ) -> tuple[list[dict[str, object]], dict[str, _LocalActionBinding]]:
        capabilities: list[dict[str, object]] = []
        bindings: dict[str, _LocalActionBinding] = {}
        resolver = self._target_resolver_factory()

        for affordance in snapshot.payload.get("affordances", []):
            if len(capabilities) >= (
                MAX_V2_ACTION_CAPABILITIES
                - len(SAFE_KEY_SEQUENCES)
                - MAX_DESKTOP_WINDOW_ACTION_CAPABILITIES
            ):
                break
            if not isinstance(affordance, Mapping):
                continue

            verb = affordance.get("name")
            target_ref = affordance.get("entity_ref")
            description = affordance.get("description")
            requires_confirmation = affordance.get("requires_confirmation")
            if (
                verb not in {"click", "write_text"}
                or not isinstance(target_ref, str)
                or not isinstance(description, str)
                or not isinstance(requires_confirmation, bool)
            ):
                continue

            try:
                element = snapshot.reference_map.resolve(
                    target_ref,
                    task_id=task_id,
                    world_revision=world_revision,
                )
            except (KeyError, ValueError):
                continue

            if not self._is_unique_target(scene, resolver, element):
                continue

            if verb == "click":
                if not self._is_clickable_target(element):
                    continue
            elif not self._is_editable_uia_target(element):
                continue

            capability_name = f"{verb}_{target_ref}"
            if capability_name in bindings:
                continue

            capabilities.append(
                {
                    "name": capability_name,
                    "description": description,
                    "target_ref": target_ref,
                    "requires_confirmation": requires_confirmation,
                }
            )
            bindings[capability_name] = _LocalActionBinding(
                action_name=capability_name,
                target_ref=target_ref,
                semantic_action=verb,
                requires_confirmation=requires_confirmation,
            )

        window_actions_added = 0
        for target_ref in snapshot.reference_map.refs:
            if window_actions_added >= MAX_DESKTOP_WINDOW_ACTION_CAPABILITIES:
                break
            if len(capabilities) >= (
                MAX_V2_ACTION_CAPABILITIES - len(SAFE_KEY_SEQUENCES)
            ):
                break
            try:
                element = snapshot.reference_map.resolve(
                    target_ref,
                    task_id=task_id,
                    world_revision=world_revision,
                )
            except (KeyError, ValueError):
                continue

            metadata = element.metadata or {}
            handle = metadata.get("window_handle")
            if (
                metadata.get("source") != "windows_desktop_window"
                or isinstance(handle, bool)
                or not isinstance(handle, int)
                or handle <= 0
                or metadata.get("is_visible") is not True
                or metadata.get("is_foreground") is not False
                or not self._is_unique_target(scene, resolver, element)
            ):
                continue

            capability_name = f"activate_window_{target_ref}"
            if capability_name in bindings:
                continue
            label = element.label.strip() if isinstance(element.label, str) else ""
            if not label:
                continue

            capabilities.append(
                {
                    "name": capability_name,
                    "description": (
                        f"Activate the visible desktop window '{label}'. "
                        "Its native window identity is resolved locally."
                    ),
                    "target_ref": target_ref,
                    "requires_confirmation": False,
                }
            )
            bindings[capability_name] = _LocalActionBinding(
                action_name=capability_name,
                target_ref=target_ref,
                semantic_action="activate_window",
                requires_confirmation=False,
                value=str(handle),
            )
            window_actions_added += 1

        for sequence in SAFE_KEY_SEQUENCES:
            if len(capabilities) >= MAX_V2_ACTION_CAPABILITIES:
                break
            slug = sequence.replace("+", "_")
            capability_name = f"press_key_{slug}"
            if capability_name in bindings:
                continue
            capabilities.append(
                {
                    "name": capability_name,
                    "description": (
                        f"Press the allowlisted '{sequence}' navigation "
                        "key sequence on the active desktop window."
                    ),
                    "target_ref": None,
                    "requires_confirmation": False,
                }
            )
            bindings[capability_name] = _LocalActionBinding(
                action_name=capability_name,
                target_ref=None,
                semantic_action="press_key",
                requires_confirmation=False,
                value=sequence,
            )

        return capabilities, bindings

    @staticmethod
    def _is_unique_target(
        scene: ScreenScene,
        resolver: TargetResolver,
        element: ScreenElement,
    ) -> bool:
        if not isinstance(element.label, str) or not element.label.strip():
            return False
        resolution = resolver.resolve(scene, element.label)
        return resolution.resolved and resolution.element is element

    @staticmethod
    def _is_clickable_target(element: ScreenElement) -> bool:
        if element.interaction_capability is not InteractionCapability.CLICKABLE:
            return False
        metadata = element.metadata or {}
        if metadata.get("uia_enabled") is False or metadata.get("uia_visible") is False:
            return False

        source = metadata.get("source")
        has_uia = (
            isinstance(source, str)
            and source in _UIA_SOURCES
            and metadata.get("uia_enabled") is True
            and metadata.get("uia_visible") is True
            and isinstance(metadata.get("uia_runtime_id"), str)
            and bool(metadata.get("uia_runtime_id", "").strip())
        )
        tracked_id = metadata.get("tracked_object_id")
        has_visual_target = isinstance(tracked_id, str) and bool(tracked_id.strip())
        return has_uia or has_visual_target

    @staticmethod
    def _is_editable_uia_target(element: ScreenElement) -> bool:
        metadata = element.metadata or {}
        source = metadata.get("source")
        control_type_value = metadata.get("uia_control_type") or element.kind
        control_type = (
            control_type_value.strip().casefold()
            if isinstance(control_type_value, str)
            else ""
        )
        return (
            isinstance(source, str)
            and source in _UIA_SOURCES
            and metadata.get("uia_enabled") is True
            and metadata.get("uia_visible") is True
            and isinstance(metadata.get("uia_runtime_id"), str)
            and bool(metadata.get("uia_runtime_id", "").strip())
            and control_type in {"edit", "combobox"}
            and element.interaction_capability is InteractionCapability.CLICKABLE
        )
