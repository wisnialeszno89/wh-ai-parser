"""Provider-neutral request/response contract for the NaviMind agent protocol v2.

This module is deliberately separate from the v1 bridge. It validates semantic
references and bounded JSON data only; it does not resolve references or execute
observations/actions. Those remain local-runtime responsibilities.
"""

from collections.abc import Mapping
from dataclasses import dataclass, field
import json
import math
import re
from typing import Any


MAX_BODY_BYTES = 256 * 1024
MAX_ENTITIES = 200
MAX_RELATIONSHIPS = 400
MAX_AFFORDANCES = 200
MAX_EVIDENCE_ITEMS = 100
MAX_CAPABILITIES = 64
MAX_EXPERIENCE_ITEMS = 20
MAX_TEXT_LENGTH = 8_000
MAX_REF_LENGTH = 128
MAX_OBSERVATION_ITEMS = 50

_REF_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9_-]{0,127}$")
_FORBIDDEN_KEYS = frozenset(
    {
        "x",
        "y",
        "left",
        "top",
        "right",
        "bottom",
        "hwnd",
        "window_handle",
        "runtime_id",
        "automation_id",
        "selector",
        "selectors",
        "provider_id",
        "native_id",
        "executor",
        "coordinates",
        "screen_coordinates",
        "screen_coordinate",
    }
)
_OBSERVATION_CONTRACTS = frozenset(
    {"entity_inspection_v1", "children_page_v1", "table_page_v1"}
)
_SUPPORTED_POSTCONDITIONS = frozenset(
    {
        "entity_present",
        "entity_value_equals",
        "entity_state_equals",
        "relationship_exists",
        "application_state_equals",
        "scene_changed",
    }
)


def _fail(message: str) -> None:
    raise ValueError(f"agent_task_v2:{message}")


def _object(
    value: object,
    name: str,
    *,
    allowed: set[str] | frozenset[str] | None = None,
    required: set[str] | frozenset[str] = frozenset(),
) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        _fail(f"{name}_must_be_object")
    keys = set(value.keys())
    if not all(isinstance(key, str) for key in keys):
        _fail(f"{name}_keys_must_be_strings")
    if allowed is not None:
        extra = keys - set(allowed)
        if extra:
            _fail(f"{name}_unknown_fields:{','.join(sorted(extra))}")
    missing = set(required) - keys
    if missing:
        _fail(f"{name}_missing_fields:{','.join(sorted(missing))}")
    return value


def _text(
    value: object,
    name: str,
    maximum: int,
    *,
    nullable: bool = False,
    nonempty: bool = True,
) -> None:
    if nullable and value is None:
        return
    if not isinstance(value, str):
        _fail(f"{name}_must_be_text")
    if len(value) > maximum:
        _fail(f"{name}_too_long")
    if nonempty and not value.strip():
        _fail(f"{name}_must_not_be_empty")


def _integer(value: object, name: str, minimum: int, maximum: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        _fail(f"{name}_must_be_integer")
    if value < minimum or value > maximum:
        _fail(f"{name}_out_of_bounds")


def _number(value: object, name: str, minimum: float, maximum: float) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        _fail(f"{name}_must_be_number")
    if not math.isfinite(float(value)) or value < minimum or value > maximum:
        _fail(f"{name}_out_of_bounds")


def _ref(value: object, name: str) -> str:
    _text(value, name, MAX_REF_LENGTH)
    if not _REF_PATTERN.fullmatch(value):
        _fail(f"{name}_invalid_format")
    return value


def _ref_list(value: object, name: str, maximum: int) -> set[str]:
    if not isinstance(value, list) or len(value) > maximum:
        _fail(f"{name}_invalid_list")
    refs = [_ref(item, name) for item in value]
    if len(refs) != len(set(refs)):
        _fail(f"{name}_contains_duplicates")
    return set(refs)


def _json_value(value: object, name: str, depth: int = 0) -> None:
    if depth > 5:
        _fail(f"{name}_too_deep")
    if value is None or isinstance(value, (str, bool, int)):
        if isinstance(value, str) and len(value) > 4_000:
            _fail(f"{name}_text_too_long")
        return
    if isinstance(value, float):
        if not math.isfinite(value):
            _fail(f"{name}_non_finite_number")
        return
    if isinstance(value, list):
        if len(value) > 100:
            _fail(f"{name}_list_too_large")
        for index, item in enumerate(value):
            _json_value(item, f"{name}[{index}]", depth + 1)
        return
    if isinstance(value, Mapping):
        if len(value) > 50:
            _fail(f"{name}_object_too_large")
        for key, item in value.items():
            if not isinstance(key, str) or len(key) > 128:
                _fail(f"{name}_invalid_key")
            normalized = key.strip().casefold().replace("-", "_")
            if normalized in _FORBIDDEN_KEYS:
                _fail(f"{name}_contains_provider_field:{normalized}")
            _json_value(item, f"{name}.{key}", depth + 1)
        return
    _fail(f"{name}_contains_non_json_value")


def _validate_task_state(value: object) -> None:
    state = _object(
        value,
        "task_state",
        allowed={"cycle", "max_cycles", "reasoning_calls_remaining"},
        required={"cycle", "max_cycles", "reasoning_calls_remaining"},
    )
    _integer(state["cycle"], "task_state.cycle", 0, 1_000)
    _integer(state["max_cycles"], "task_state.max_cycles", 1, 1_000)
    _integer(
        state["reasoning_calls_remaining"],
        "task_state.reasoning_calls_remaining",
        0,
        100,
    )
    if state["cycle"] > state["max_cycles"]:
        _fail("task_state_cycle_exceeds_max")


def _validate_entity(value: object) -> str:
    entity = _object(
        value,
        "world_entity",
        allowed={
            "ref",
            "type",
            "label",
            "state",
            "attributes",
            "confidence",
            "evidence_refs",
        },
        required={
            "ref",
            "type",
            "label",
            "state",
            "attributes",
            "confidence",
            "evidence_refs",
        },
    )
    ref = _ref(entity["ref"], "entity.ref")
    _text(entity["type"], "entity.type", 128)
    _text(entity["label"], "entity.label", 1_000, nullable=True)
    _object(entity["state"], "entity.state")
    _json_value(entity["state"], "entity.state")
    attributes = entity["attributes"]
    if not isinstance(attributes, list) or len(attributes) > 32:
        _fail("entity.attributes_invalid")
    attribute_names: set[str] = set()
    for attribute in attributes:
        item = _object(
            attribute,
            "entity.attribute",
            allowed={"name", "value"},
            required={"name", "value"},
        )
        _text(item["name"], "entity.attribute.name", 128)
        if item["name"] in attribute_names:
            _fail("entity.attribute_duplicate_name")
        attribute_names.add(item["name"])
        _json_value(item["value"], "entity.attribute.value")
    _number(entity["confidence"], "entity.confidence", 0, 1)
    _ref_list(entity["evidence_refs"], "entity.evidence_refs", 32)
    return ref


def _validate_evidence(value: object, world_revision: int) -> str:
    evidence = _object(
        value,
        "world_evidence",
        allowed={
            "ref",
            "source",
            "observed_at",
            "world_revision",
            "scope",
            "confidence",
            "content",
            "limitations",
            "redactions",
        },
        required={
            "ref",
            "source",
            "observed_at",
            "world_revision",
            "scope",
            "confidence",
            "content",
            "limitations",
        },
    )
    ref = _ref(evidence["ref"], "evidence.ref")
    _text(evidence["source"], "evidence.source", 64)
    _text(evidence["observed_at"], "evidence.observed_at", 64)
    _integer(evidence["world_revision"], "evidence.world_revision", 0, world_revision)
    _text(evidence["scope"], "evidence.scope", 512)
    if evidence["confidence"] is not None:
        _number(evidence["confidence"], "evidence.confidence", 0, 1)
    _object(evidence["content"], "evidence.content")
    _json_value(evidence["content"], "evidence.content")
    limitations = evidence["limitations"]
    if not isinstance(limitations, list) or len(limitations) > 16:
        _fail("evidence.limitations_invalid")
    for item in limitations:
        _text(item, "evidence.limitation", 1_000)
    if "redactions" in evidence:
        redactions = evidence["redactions"]
        if not isinstance(redactions, list) or len(redactions) > 32:
            _fail("evidence.redactions_invalid")
        for item in redactions:
            _text(item, "evidence.redaction", 256)
    return ref


def _validate_world(value: object) -> tuple[int, set[str], set[str]]:
    world = _object(
        value,
        "world",
        allowed={
            "revision",
            "observed_at",
            "application",
            "window_title",
            "entities",
            "relationships",
            "affordances",
            "evidence",
        },
        required={
            "revision",
            "observed_at",
            "application",
            "window_title",
            "entities",
            "relationships",
            "affordances",
            "evidence",
        },
    )
    revision = world["revision"]
    _integer(revision, "world.revision", 0, 2_000_000_000)
    _text(world["observed_at"], "world.observed_at", 64)
    _text(world["application"], "world.application", 256, nullable=True)
    _text(world["window_title"], "world.window_title", 2_000, nullable=True)

    entities = world["entities"]
    if not isinstance(entities, list) or len(entities) > MAX_ENTITIES:
        _fail("world.entities_invalid")
    entity_refs = [_validate_entity(item) for item in entities]
    if len(entity_refs) != len(set(entity_refs)):
        _fail("world.entity_refs_duplicate")
    entity_ref_set = set(entity_refs)

    evidence = world["evidence"]
    if not isinstance(evidence, list) or len(evidence) > MAX_EVIDENCE_ITEMS:
        _fail("world.evidence_invalid")
    evidence_refs = [_validate_evidence(item, revision) for item in evidence]
    if len(evidence_refs) != len(set(evidence_refs)):
        _fail("world.evidence_refs_duplicate")
    evidence_ref_set = set(evidence_refs)

    for entity in entities:
        refs = _ref_list(entity["evidence_refs"], "entity.evidence_refs", 32)
        if not refs.issubset(evidence_ref_set):
            _fail("entity.references_unknown_evidence")

    relationships = world["relationships"]
    if (
        not isinstance(relationships, list)
        or len(relationships) > MAX_RELATIONSHIPS
    ):
        _fail("world.relationships_invalid")
    for relationship in relationships:
        item = _object(
            relationship,
            "world.relationship",
            allowed={
                "from_ref",
                "relationship",
                "to_ref",
                "confidence",
                "evidence_refs",
            },
            required={
                "from_ref",
                "relationship",
                "to_ref",
                "confidence",
                "evidence_refs",
            },
        )
        from_ref = _ref(item["from_ref"], "relationship.from_ref")
        to_ref = _ref(item["to_ref"], "relationship.to_ref")
        if from_ref not in entity_ref_set or to_ref not in entity_ref_set:
            _fail("relationship.references_unknown_entity")
        _text(item["relationship"], "relationship.name", 128)
        _number(item["confidence"], "relationship.confidence", 0, 1)
        refs = _ref_list(item["evidence_refs"], "relationship.evidence_refs", 32)
        if not refs.issubset(evidence_ref_set):
            _fail("relationship.references_unknown_evidence")

    affordances = world["affordances"]
    if not isinstance(affordances, list) or len(affordances) > MAX_AFFORDANCES:
        _fail("world.affordances_invalid")
    affordance_ids: set[str] = set()
    for affordance in affordances:
        item = _object(
            affordance,
            "world.affordance",
            allowed={
                "id",
                "entity_ref",
                "name",
                "description",
                "requires_confirmation",
            },
            required={
                "id",
                "entity_ref",
                "name",
                "description",
                "requires_confirmation",
            },
        )
        affordance_id = _ref(item["id"], "affordance.id")
        if affordance_id in affordance_ids:
            _fail("world.affordance_ids_duplicate")
        affordance_ids.add(affordance_id)
        entity_ref = _ref(item["entity_ref"], "affordance.entity_ref")
        if entity_ref not in entity_ref_set:
            _fail("affordance.references_unknown_entity")
        _text(item["name"], "affordance.name", 128)
        _text(item["description"], "affordance.description", 1_000)
        if not isinstance(item["requires_confirmation"], bool):
            _fail("affordance.requires_confirmation_must_be_boolean")

    return revision, entity_ref_set, evidence_ref_set


def _validate_capabilities(
    value: object,
    entity_refs: set[str],
    constraints: Mapping[str, object],
) -> tuple[dict[str, Mapping[str, object]], dict[str, Mapping[str, object]]]:
    capabilities = _object(
        value,
        "capabilities",
        allowed={"observations", "actions"},
        required={"observations", "actions"},
    )
    observations = capabilities["observations"]
    actions = capabilities["actions"]
    if (
        not isinstance(observations, list)
        or len(observations) > MAX_CAPABILITIES
    ):
        _fail("capabilities.observations_invalid")
    if not isinstance(actions, list) or len(actions) > MAX_CAPABILITIES:
        _fail("capabilities.actions_invalid")

    observation_map: dict[str, Mapping[str, object]] = {}
    for capability in observations:
        item = _object(
            capability,
            "observation_capability",
            allowed={
                "id",
                "description",
                "target_ref",
                "input_contract",
                "max_items",
                "data_classification",
                "read_only",
            },
            required={
                "id",
                "description",
                "target_ref",
                "input_contract",
                "max_items",
                "data_classification",
                "read_only",
            },
        )
        capability_id = _ref(item["id"], "observation_capability.id")
        if capability_id in observation_map:
            _fail("capabilities.observation_ids_duplicate")
        target_ref = _ref(item["target_ref"], "observation_capability.target_ref")
        if target_ref not in entity_refs:
            _fail("observation_capability.references_unknown_entity")
        _text(item["description"], "observation_capability.description", 1_000)
        _text(item["input_contract"], "observation_capability.input_contract", 64)
        if item["input_contract"] not in _OBSERVATION_CONTRACTS:
            _fail("observation_capability.unsupported_input_contract")
        _integer(item["max_items"], "observation_capability.max_items", 1, MAX_OBSERVATION_ITEMS)
        if item["max_items"] > constraints["max_observation_items"]:
            _fail("observation_capability.exceeds_task_budget")
        _text(item["data_classification"], "observation_capability.data_classification", 64)
        if item["read_only"] is not True:
            _fail("observation_capability_must_be_read_only")
        observation_map[capability_id] = item

    action_map: dict[str, Mapping[str, object]] = {}
    for action in actions:
        item = _object(
            action,
            "action_capability",
            allowed={"name", "description", "target_ref", "requires_confirmation"},
            required={"name", "description", "target_ref", "requires_confirmation"},
        )
        name = item["name"]
        _text(name, "action_capability.name", 128)
        if name in action_map:
            _fail("capabilities.action_names_duplicate")
        _text(item["description"], "action_capability.description", 1_000)
        target_ref = item["target_ref"]
        if target_ref is not None:
            target_ref = _ref(target_ref, "action_capability.target_ref")
            if target_ref not in entity_refs:
                _fail("action_capability.references_unknown_entity")
        if not isinstance(item["requires_confirmation"], bool):
            _fail("action_capability.requires_confirmation_must_be_boolean")
        action_map[name] = item

    return observation_map, action_map


def _validate_constraints(value: object) -> Mapping[str, object]:
    constraints = _object(
        value,
        "constraints",
        allowed={
            "max_observations_per_cycle",
            "max_observation_items",
            "max_evidence_bytes",
            "semantic_only",
            "verify_each_action",
        },
        required={
            "max_observations_per_cycle",
            "max_observation_items",
            "max_evidence_bytes",
            "semantic_only",
            "verify_each_action",
        },
    )
    _integer(constraints["max_observations_per_cycle"], "constraints.max_observations_per_cycle", 1, 1)
    _integer(constraints["max_observation_items"], "constraints.max_observation_items", 1, MAX_OBSERVATION_ITEMS)
    _integer(constraints["max_evidence_bytes"], "constraints.max_evidence_bytes", 1_024, 32_768)
    if constraints["semantic_only"] is not True:
        _fail("constraints.semantic_only_must_be_true")
    if constraints["verify_each_action"] is not True:
        _fail("constraints.verify_each_action_must_be_true")
    return constraints


def validate_agent_task_v2_payload(value: object) -> None:
    """Validate a v2 request. Raises ValueError for any unsafe or invalid shape."""
    payload = _object(
        value,
        "request",
        allowed={
            "version",
            "task_id",
            "goal",
            "intent",
            "session_id",
            "task_state",
            "world",
            "capabilities",
            "knowledge",
            "experience",
            "constraints",
            "metadata",
        },
        required={
            "version",
            "task_id",
            "goal",
            "intent",
            "session_id",
            "task_state",
            "world",
            "capabilities",
            "knowledge",
            "experience",
            "constraints",
            "metadata",
        },
    )
    if payload["version"] != "2":
        _fail("unsupported_version")
    _text(payload["task_id"], "task_id", 256)
    _text(payload["goal"], "goal", MAX_TEXT_LENGTH)
    _text(payload["intent"], "intent", 256)
    _text(payload["session_id"], "session_id", 256, nullable=True)
    _validate_task_state(payload["task_state"])
    constraints = _validate_constraints(payload["constraints"])
    _, entity_refs, evidence_refs = _validate_world(payload["world"])
    _validate_capabilities(
        payload["capabilities"],
        entity_refs,
        constraints,
    )

    if payload["knowledge"] is not None:
        _object(payload["knowledge"], "knowledge")
        _json_value(payload["knowledge"], "knowledge")
    experience = payload["experience"]
    if not isinstance(experience, list) or len(experience) > MAX_EXPERIENCE_ITEMS:
        _fail("experience_invalid")
    for item in experience:
        _object(item, "experience_item")
        _json_value(item, "experience_item")
    _object(payload["metadata"], "metadata")
    _json_value(payload["metadata"], "metadata")

    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
    ).encode("utf-8")
    if len(encoded) > MAX_BODY_BYTES:
        _fail("request_body_too_large")


def _validate_observation_parameters(
    parameters: object,
    capability: Mapping[str, object],
    constraints: Mapping[str, object],
) -> None:
    contract = capability["input_contract"]
    if contract == "table_page_v1":
        item = _object(
            parameters,
            "observation.parameters",
            allowed={"offset", "limit", "text_query"},
            required={"offset", "limit"},
        )
        _integer(item["offset"], "observation.offset", 0, 100_000)
        _integer(item["limit"], "observation.limit", 1, int(capability["max_items"]))
        _integer(item["limit"], "observation.limit", 1, int(constraints["max_observation_items"]))
        if "text_query" in item:
            _text(item["text_query"], "observation.text_query", 300)
        return
    if contract == "entity_inspection_v1":
        item = _object(
            parameters,
            "observation.parameters",
            allowed={"fields"},
            required={"fields"},
        )
        fields = item["fields"]
        if not isinstance(fields, list) or len(fields) > 20:
            _fail("observation.fields_invalid")
        for field_name in fields:
            _text(field_name, "observation.field", 128)
        if len(fields) != len(set(fields)):
            _fail("observation.fields_duplicate")
        return
    if contract == "children_page_v1":
        item = _object(
            parameters,
            "observation.parameters",
            allowed={"depth", "offset", "limit"},
            required={"depth", "offset", "limit"},
        )
        _integer(item["depth"], "observation.depth", 1, 3)
        _integer(item["offset"], "observation.offset", 0, 100_000)
        _integer(item["limit"], "observation.limit", 1, int(capability["max_items"]))
        _integer(item["limit"], "observation.limit", 1, int(constraints["max_observation_items"]))
        return
    _fail("observation.unsupported_input_contract")


def _validate_postcondition(value: object, entity_refs: set[str]) -> None:
    item = _object(
        value,
        "action.expected_postcondition",
        allowed={
            "kind",
            "target_ref",
            "expected_value",
            "expected_value_ref",
            "state",
            "from_ref",
            "relationship",
            "to_ref",
            "application",
        },
        required={"kind"},
    )
    kind = item["kind"]
    if kind not in _SUPPORTED_POSTCONDITIONS:
        _fail("action.unsupported_postcondition")
    if kind in {"entity_present", "entity_value_equals", "entity_state_equals"}:
        target_ref = _ref(item.get("target_ref"), "postcondition.target_ref")
        if target_ref not in entity_refs:
            _fail("postcondition.references_unknown_entity")
    if kind == "entity_value_equals":
        has_value = "expected_value" in item
        has_ref = "expected_value_ref" in item
        if has_value == has_ref:
            _fail("postcondition.value_or_ref_required")
        if has_ref:
            _ref(item["expected_value_ref"], "postcondition.expected_value_ref")
        else:
            _json_value(item["expected_value"], "postcondition.expected_value")
    if kind == "entity_state_equals":
        _text(item.get("state"), "postcondition.state", 128)
        if "expected_value" not in item:
            _fail("postcondition.expected_value_required")
        _json_value(item["expected_value"], "postcondition.expected_value")
    if kind == "scene_changed" and set(item) != {"kind"}:
        _fail("postcondition.scene_changed_fields_invalid")
    if kind == "relationship_exists":
        from_ref = _ref(item.get("from_ref"), "postcondition.from_ref")
        to_ref = _ref(item.get("to_ref"), "postcondition.to_ref")
        if from_ref not in entity_refs or to_ref not in entity_refs:
            _fail("postcondition.references_unknown_entity")
        _text(item.get("relationship"), "postcondition.relationship", 128)
    if kind == "application_state_equals":
        _text(item.get("application"), "postcondition.application", 256)
        if "expected_value" not in item:
            _fail("postcondition.expected_value_required")
        _json_value(item["expected_value"], "postcondition.expected_value")


def validate_agent_task_v2_response(
    candidate: object,
    request: Mapping[str, object],
) -> None:
    """Validate one v2 decision against the exact request that elicited it."""
    validate_agent_task_v2_payload(request)
    response = _object(
        candidate,
        "response",
        allowed={
            "version",
            "task_id",
            "decision",
            "rationale",
            "confidence",
            "observation_request",
            "action",
            "completion",
            "requires_manual_review",
        },
        required={
            "version",
            "task_id",
            "decision",
            "rationale",
            "confidence",
            "observation_request",
            "action",
            "completion",
            "requires_manual_review",
        },
    )
    if response["version"] != "2" or response["version"] != request["version"]:
        _fail("response_version_mismatch")
    if response["task_id"] != request["task_id"]:
        _fail("response_task_id_mismatch")
    decision = response["decision"]
    if decision not in {"observe", "act", "done", "manual_review"}:
        _fail("unsupported_decision")
    _text(response["rationale"], "response.rationale", 2_000)
    _number(response["confidence"], "response.confidence", 0, 1)
    if not isinstance(response["requires_manual_review"], bool):
        _fail("response.requires_manual_review_must_be_boolean")

    world = request["world"]
    revision, entity_refs, evidence_refs = _validate_world(world)
    constraints = request["constraints"]
    capabilities = request["capabilities"]
    observation_map, action_map = _validate_capabilities(
        capabilities,
        entity_refs,
        constraints,
    )

    observation_request = response["observation_request"]
    action = response["action"]
    completion = response["completion"]
    if decision == "observe":
        if action is not None or completion is not None:
            _fail("observe_has_incompatible_payload")
        if response["requires_manual_review"]:
            _fail("observe_cannot_require_manual_review")
        item = _object(
            observation_request,
            "observation_request",
            allowed={
                "capability_id",
                "target_ref",
                "parameters",
                "based_on_world_revision",
            },
            required={
                "capability_id",
                "target_ref",
                "parameters",
                "based_on_world_revision",
            },
        )
        capability_id = _ref(item["capability_id"], "observation.capability_id")
        capability = observation_map.get(capability_id)
        if capability is None:
            _fail("observation_capability_not_exposed")
        if item["target_ref"] != capability["target_ref"]:
            _fail("observation_target_mismatch")
        _integer(item["based_on_world_revision"], "observation.world_revision", revision, revision)
        _validate_observation_parameters(item["parameters"], capability, constraints)
        return

    if decision == "act":
        if observation_request is not None or completion is not None:
            _fail("act_has_incompatible_payload")
        if response["requires_manual_review"]:
            _fail("act_cannot_require_manual_review")
        item = _object(
            action,
            "action",
            allowed={
                "name",
                "target_ref",
                "value",
                "expected_postcondition",
                "requires_confirmation",
            },
            required={
                "name",
                "target_ref",
                "value",
                "expected_postcondition",
                "requires_confirmation",
            },
        )
        _text(item["name"], "action.name", 128)
        capability = action_map.get(item["name"])
        if capability is None:
            _fail("action_not_exposed")
        target_ref = item["target_ref"]
        if target_ref is not None:
            target_ref = _ref(target_ref, "action.target_ref")
            if target_ref not in entity_refs:
                _fail("action.references_unknown_entity")
        if capability["target_ref"] != target_ref:
            _fail("action_target_mismatch")
        _text(item["value"], "action.value", 2_000, nullable=True, nonempty=False)
        if not isinstance(item["requires_confirmation"], bool):
            _fail("action.requires_confirmation_must_be_boolean")
        if capability["requires_confirmation"] and not item["requires_confirmation"]:
            _fail("action_confirmation_cannot_be_downgraded")
        _validate_postcondition(item["expected_postcondition"], entity_refs)
        return

    if decision == "done":
        if observation_request is not None or action is not None or completion is None:
            _fail("done_has_incompatible_payload")
        if response["requires_manual_review"]:
            _fail("done_cannot_require_manual_review")
        item = _object(
            completion,
            "completion",
            allowed={"evidence_refs"},
            required={"evidence_refs"},
        )
        refs = _ref_list(item["evidence_refs"], "completion.evidence_refs", 32)
        if not refs:
            _fail("done_requires_evidence")
        if not refs.issubset(evidence_refs):
            _fail("done_references_unknown_evidence")
        return

    if observation_request is not None or action is not None or completion is not None:
        _fail("manual_review_has_incompatible_payload")
    if not response["requires_manual_review"]:
        _fail("manual_review_flag_required")


@dataclass(frozen=True)
class AgentTaskV2Contract:
    """Immutable envelope for one bounded NaviMind v2 reasoning cycle."""

    task_id: str
    goal: str
    intent: str
    task_state: Mapping[str, object]
    world: Mapping[str, object]
    capabilities: Mapping[str, object]
    session_id: str | None = None
    knowledge: Mapping[str, object] | None = None
    experience: tuple[Mapping[str, object], ...] = ()
    constraints: Mapping[str, object] = field(
        default_factory=lambda: {
            "max_observations_per_cycle": 1,
            "max_observation_items": 50,
            "max_evidence_bytes": 32_768,
            "semantic_only": True,
            "verify_each_action": True,
        }
    )
    metadata: Mapping[str, object] = field(default_factory=dict)
    version: str = "2"

    def to_payload(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "version": self.version,
            "task_id": self.task_id,
            "goal": self.goal,
            "intent": self.intent,
            "session_id": self.session_id,
            "task_state": dict(self.task_state),
            "world": dict(self.world),
            "capabilities": dict(self.capabilities),
            "knowledge": (
                dict(self.knowledge)
                if self.knowledge is not None
                else None
            ),
            "experience": [dict(item) for item in self.experience],
            "constraints": dict(self.constraints),
            "metadata": dict(self.metadata),
        }
        validate_agent_task_v2_payload(payload)
        return json.loads(json.dumps(payload, ensure_ascii=False, allow_nan=False))

    @classmethod
    def from_payload(cls, payload: Mapping[str, object]) -> "AgentTaskV2Contract":
        validate_agent_task_v2_payload(payload)
        return cls(
            task_id=str(payload["task_id"]),
            goal=str(payload["goal"]),
            intent=str(payload["intent"]),
            session_id=payload["session_id"],
            task_state=dict(payload["task_state"]),
            world=dict(payload["world"]),
            capabilities=dict(payload["capabilities"]),
            knowledge=(
                dict(payload["knowledge"])
                if payload["knowledge"] is not None
                else None
            ),
            experience=tuple(dict(item) for item in payload["experience"]),
            constraints=dict(payload["constraints"]),
            metadata=dict(payload["metadata"]),
            version=str(payload["version"]),
        )
