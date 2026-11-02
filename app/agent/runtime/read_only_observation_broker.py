"""Local read-only observation capability registry and broker for agent protocol v2.

The broker is the local authority for observation requests. NaviMind can select
only capabilities explicitly bound by the runtime to the current task/revision.
It never receives provider IDs or executable handlers.
"""

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
import json
import math
import time
from typing import Protocol

from app.agent.bridge.agent_task_v2_world_builder import (
    AgentTaskV2WorldSnapshot,
)
from app.agent.perception.screen_element import ScreenElement


SUPPORTED_INPUT_CONTRACTS = frozenset(
    {
        "entity_inspection_v1",
        "children_page_v1",
        "table_page_v1",
    }
)

MAX_CAPABILITY_ITEMS = 50
MAX_RESULT_BYTES = 32_768
MAX_EVIDENCE_TEXT = 2_000
MAX_TABLE_COLUMNS = 64
MAX_TABLE_CELL_TEXT = 1_000


class ObservationRejected(ValueError):
    """A v2 read-only observation request was rejected by local policy."""


@dataclass(frozen=True)
class ObservationCapabilitySpec:
    """A local code-defined observation capability, not model-provided data."""

    name: str
    description: str
    input_contract: str
    max_items: int
    data_classification: str
    evidence_source: str
    timeout_seconds: float = 3.0
    max_result_bytes: int = 8_192
    read_only: bool = True

    def __post_init__(self) -> None:
        if not self.name or len(self.name) > 128:
            raise ValueError("observation_capability_invalid_name")
        if not self.description or len(self.description) > 1_000:
            raise ValueError("observation_capability_invalid_description")
        if self.input_contract not in SUPPORTED_INPUT_CONTRACTS:
            raise ValueError("observation_capability_unsupported_input_contract")
        if isinstance(self.max_items, bool) or not 1 <= self.max_items <= MAX_CAPABILITY_ITEMS:
            raise ValueError("observation_capability_invalid_max_items")
        if not self.data_classification or len(self.data_classification) > 64:
            raise ValueError("observation_capability_invalid_classification")
        if not self.evidence_source or len(self.evidence_source) > 64:
            raise ValueError("observation_capability_invalid_evidence_source")
        if not math.isfinite(self.timeout_seconds) or not 0 < self.timeout_seconds <= 10:
            raise ValueError("observation_capability_invalid_timeout")
        if isinstance(self.max_result_bytes, bool) or not 1_024 <= self.max_result_bytes <= MAX_RESULT_BYTES:
            raise ValueError("observation_capability_invalid_result_bytes")
        if self.read_only is not True:
            raise ValueError("observation_capability_must_be_read_only")


@dataclass(frozen=True)
class ObservationReadContext:
    """Runtime-only bounds passed to a registered read handler."""

    task_id: str
    world_revision: int
    max_items: int
    max_result_bytes: int
    deadline_monotonic: float


@dataclass(frozen=True)
class ObservationReadResult:
    """Structured result returned by one local read-only adapter."""

    content: Mapping[str, object]
    limitations: tuple[str, ...] = ()
    confidence: float | None = None


class ObservationReader(Protocol):
    def __call__(
        self,
        target: ScreenElement,
        parameters: Mapping[str, object],
        context: ObservationReadContext,
    ) -> ObservationReadResult:
        """Read bounded information without mutating application state."""
        ...


@dataclass(frozen=True)
class _RegisteredReader:
    spec: ObservationCapabilitySpec
    reader: ObservationReader


@dataclass(frozen=True)
class _BoundCapability:
    capability_id: str
    target_ref: str
    task_id: str
    world_revision: int
    target: ScreenElement
    registered: _RegisteredReader


def _fail(reason: str) -> None:
    raise ObservationRejected(f"observation_rejected:{reason}")


def _bounded_text(value: object, name: str, maximum: int) -> None:
    if not isinstance(value, str) or not value.strip() or len(value) > maximum:
        _fail(f"invalid_{name}")


def _bounded_int(value: object, name: str, minimum: int, maximum: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        _fail(f"invalid_{name}")
    if value < minimum or value > maximum:
        _fail(f"{name}_out_of_bounds")


def _validate_parameters(
    input_contract: str,
    parameters: object,
    *,
    capability_max_items: int,
    task_max_items: int,
) -> Mapping[str, object]:
    if not isinstance(parameters, Mapping):
        _fail("parameters_must_be_object")

    if input_contract == "table_page_v1":
        allowed = {"offset", "limit", "text_query"}
        required = {"offset", "limit"}
        if set(parameters) - allowed or not required.issubset(parameters):
            _fail("table_page_parameters_invalid")
        _bounded_int(parameters["offset"], "offset", 0, 100_000)
        _bounded_int(
            parameters["limit"],
            "limit",
            1,
            min(capability_max_items, task_max_items),
        )
        if "text_query" in parameters:
            if not isinstance(parameters["text_query"], str) or len(parameters["text_query"]) > 300:
                _fail("invalid_text_query")
        return dict(parameters)

    if input_contract == "entity_inspection_v1":
        if set(parameters) != {"fields"}:
            _fail("entity_inspection_parameters_invalid")
        fields = parameters["fields"]
        if not isinstance(fields, list) or len(fields) > 20:
            _fail("invalid_fields")
        for field_name in fields:
            _bounded_text(field_name, "field_name", 128)
        if len(fields) != len(set(fields)):
            _fail("duplicate_fields")
        return {"fields": tuple(fields)}

    if input_contract == "children_page_v1":
        if set(parameters) != {"depth", "offset", "limit"}:
            _fail("children_page_parameters_invalid")
        _bounded_int(parameters["depth"], "depth", 1, 3)
        _bounded_int(parameters["offset"], "offset", 0, 100_000)
        _bounded_int(
            parameters["limit"],
            "limit",
            1,
            min(capability_max_items, task_max_items),
        )
        return dict(parameters)

    _fail("unsupported_input_contract")
    raise AssertionError("unreachable")


def _json_safe(value: object, *, depth: int = 0) -> object:
    if depth > 5:
        _fail("result_too_deep")
    if value is None or isinstance(value, (str, bool, int)):
        if isinstance(value, str) and len(value) > MAX_EVIDENCE_TEXT:
            _fail("result_text_too_long")
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            _fail("result_non_finite_number")
        return value
    if isinstance(value, (list, tuple)):
        if len(value) > 100:
            _fail("result_list_too_large")
        return [_json_safe(item, depth=depth + 1) for item in value]
    if isinstance(value, Mapping):
        if len(value) > 64:
            _fail("result_object_too_large")
        result: dict[str, object] = {}
        for key, item in value.items():
            if not isinstance(key, str) or not key or len(key) > 128:
                _fail("result_invalid_key")
            normalized = key.strip().casefold().replace("-", "_")
            if normalized in {
                "x", "y", "left", "top", "right", "bottom", "width", "height",
                "bounds", "position", "coordinates", "screen_coordinates",
                "hwnd", "window_handle", "runtime_id", "uia_runtime_id",
                "automation_id", "provider_id", "provider_element_id",
                "native_id", "tracked_object_id", "element_id", "selector",
                "selectors", "executor", "screenshot",
            }:
                _fail(f"result_contains_provider_field:{normalized}")
            result[key] = _json_safe(item, depth=depth + 1)
        return result
    _fail("result_contains_non_json_value")
    raise AssertionError("unreachable")


def _validate_result_shape(
    input_contract: str,
    content: Mapping[str, object],
    parameters: Mapping[str, object],
    max_items: int,
) -> dict[str, object]:
    safe = _json_safe(content)
    if not isinstance(safe, dict):
        _fail("result_content_must_be_object")

    if input_contract == "table_page_v1":
        allowed = {
            "headers",
            "rows",
            "offset",
            "has_more",
            "reported_row_count",
        }
        required = {"headers", "rows", "offset", "has_more"}
        if set(safe) - allowed or not required.issubset(safe):
            _fail("table_page_result_invalid")

        headers = safe["headers"]
        rows = safe["rows"]
        if (
            not isinstance(headers, list)
            or not 1 <= len(headers) <= MAX_TABLE_COLUMNS
            or not all(
                isinstance(header, str) and len(header) <= 128
                for header in headers
            )
        ):
            _fail("table_page_headers_invalid")
        if not isinstance(rows, list) or len(rows) > min(max_items, int(parameters["limit"])):
            _fail("table_page_rows_out_of_bounds")
        for row in rows:
            if not isinstance(row, list) or len(row) != len(headers):
                _fail("table_page_row_shape_invalid")
            for cell in row:
                if cell is not None and not isinstance(cell, (str, int, float, bool)):
                    _fail("table_page_cell_type_invalid")
                if isinstance(cell, str) and len(cell) > MAX_TABLE_CELL_TEXT:
                    _fail("table_page_cell_too_long")
        if safe["offset"] != parameters["offset"]:
            _fail("table_page_offset_mismatch")
        if not isinstance(safe["has_more"], bool):
            _fail("table_page_has_more_invalid")
        if "reported_row_count" in safe:
            count = safe["reported_row_count"]
            if count is not None:
                _bounded_int(count, "reported_row_count", 0, 1_000_000_000)
        return safe

    if input_contract == "entity_inspection_v1":
        if set(safe) != {"fields"} or not isinstance(safe["fields"], Mapping):
            _fail("entity_inspection_result_invalid")
        requested = set(parameters["fields"])
        if set(safe["fields"]) - requested:
            _fail("entity_inspection_returned_unrequested_field")
        return safe

    if input_contract == "children_page_v1":
        if set(safe) - {"items", "offset", "has_more"} or not {
            "items", "offset", "has_more"
        }.issubset(safe):
            _fail("children_page_result_invalid")
        items = safe["items"]
        if not isinstance(items, list) or len(items) > min(max_items, int(parameters["limit"])):
            _fail("children_page_items_out_of_bounds")
        if safe["offset"] != parameters["offset"] or not isinstance(safe["has_more"], bool):
            _fail("children_page_paging_invalid")
        for item in items:
            if not isinstance(item, Mapping) or set(item) - {"type", "label", "state"}:
                _fail("children_page_item_invalid")
        return safe

    _fail("unsupported_input_contract")
    raise AssertionError("unreachable")


class ReadOnlyObservationBroker:
    """Bind local readers to task-scoped refs and execute bounded read-only requests."""

    def __init__(
        self,
        *,
        authorized_data_classifications: frozenset[str] = frozenset({"ui_structure"}),
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._authorized_classifications = frozenset(
            authorized_data_classifications
        )
        self._clock = clock
        self._registered: dict[str, _RegisteredReader] = {}
        self._bindings: dict[str, _BoundCapability] = {}
        self._capability_sequence = 0
        self._evidence_sequences: dict[str, int] = {}

    def register(
        self,
        spec: ObservationCapabilitySpec,
        reader: ObservationReader,
    ) -> None:
        if spec.name in self._registered:
            raise ValueError("observation_capability_already_registered")
        if not callable(reader):
            raise TypeError("observation_reader_must_be_callable")
        self._registered[spec.name] = _RegisteredReader(spec, reader)

    def bind(
        self,
        snapshot: AgentTaskV2WorldSnapshot,
        *,
        capability_name: str,
        target_ref: str,
    ) -> dict[str, object]:
        registered = self._registered.get(capability_name)
        if registered is None:
            raise ValueError("observation_capability_not_registered")

        target = snapshot.reference_map.resolve(
            target_ref,
            task_id=snapshot.reference_map.task_id,
            world_revision=snapshot.reference_map.world_revision,
        )
        self._capability_sequence += 1
        capability_id = f"obs_{self._capability_sequence:04d}"
        binding = _BoundCapability(
            capability_id=capability_id,
            target_ref=target_ref,
            task_id=snapshot.reference_map.task_id,
            world_revision=snapshot.reference_map.world_revision,
            target=target,
            registered=registered,
        )
        self._bindings[capability_id] = binding

        spec = registered.spec
        return {
            "id": capability_id,
            "description": spec.description,
            "target_ref": target_ref,
            "input_contract": spec.input_contract,
            "max_items": spec.max_items,
            "data_classification": spec.data_classification,
            "read_only": True,
        }

    def observe(
        self,
        request: Mapping[str, object],
        *,
        task_id: str,
        world_revision: int,
        max_observation_items: int,
        max_evidence_bytes: int,
    ) -> dict[str, object]:
        """Execute exactly one previously bound, permitted observation request."""
        if not isinstance(request, Mapping):
            _fail("request_must_be_object")
        if set(request) != {
            "capability_id",
            "target_ref",
            "parameters",
            "based_on_world_revision",
        }:
            _fail("request_shape_invalid")

        capability_id = request["capability_id"]
        _bounded_text(capability_id, "capability_id", 128)
        binding = self._bindings.get(capability_id)
        if binding is None:
            _fail("capability_not_exposed")
        if binding.task_id != task_id:
            _fail("task_scope_mismatch")
        if binding.world_revision != world_revision:
            _fail("binding_stale")
        _bounded_text(request["target_ref"], "target_ref", 128)
        if request["target_ref"] != binding.target_ref:
            _fail("target_ref_mismatch")
        _bounded_int(
            request["based_on_world_revision"],
            "based_on_world_revision",
            world_revision,
            world_revision,
        )
        if (
            isinstance(max_observation_items, bool)
            or not 1 <= max_observation_items <= MAX_CAPABILITY_ITEMS
        ):
            _fail("invalid_task_item_budget")
        if (
            isinstance(max_evidence_bytes, bool)
            or not 1_024 <= max_evidence_bytes <= MAX_RESULT_BYTES
        ):
            _fail("invalid_task_byte_budget")

        spec = binding.registered.spec
        if spec.read_only is not True:
            _fail("capability_not_read_only")
        if spec.data_classification not in self._authorized_classifications:
            _fail("data_classification_not_authorized")
        parameters = _validate_parameters(
            spec.input_contract,
            request["parameters"],
            capability_max_items=spec.max_items,
            task_max_items=max_observation_items,
        )

        byte_budget = min(spec.max_result_bytes, max_evidence_bytes)
        deadline = self._clock() + spec.timeout_seconds
        context = ObservationReadContext(
            task_id=task_id,
            world_revision=world_revision,
            max_items=min(spec.max_items, max_observation_items),
            max_result_bytes=byte_budget,
            deadline_monotonic=deadline,
        )

        # The synchronous broker cannot forcibly interrupt a blocked COM call.
        # Registered adapters must pass this deadline to bounded provider calls
        # and return promptly; the broker rejects any result that arrives late.
        started = self._clock()
        try:
            result = binding.registered.reader(
                binding.target,
                parameters,
                context,
            )
        except ObservationRejected:
            raise
        except Exception as exc:
            _fail(f"reader_failed:{type(exc).__name__}")
        elapsed = self._clock() - started
        if elapsed > spec.timeout_seconds:
            _fail("observation_time_budget_exceeded")
        if not isinstance(result, ObservationReadResult):
            _fail("reader_returned_invalid_result")

        content = _validate_result_shape(
            spec.input_contract,
            result.content,
            parameters,
            context.max_items,
        )
        if result.confidence is not None and (
            isinstance(result.confidence, bool)
            or not isinstance(result.confidence, (float, int))
            or not math.isfinite(float(result.confidence))
            or not 0 <= result.confidence <= 1
        ):
            _fail("reader_confidence_invalid")
        if len(result.limitations) > 16 or not all(
            isinstance(item, str) and 0 < len(item) <= 1_000
            for item in result.limitations
        ):
            _fail("reader_limitations_invalid")

        evidence_content = dict(content)
        encoded = json.dumps(
            evidence_content,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
        ).encode("utf-8")
        if len(encoded) > byte_budget:
            _fail("observation_result_byte_budget_exceeded")

        sequence = self._evidence_sequences.get(task_id, 0) + 1
        self._evidence_sequences[task_id] = sequence
        observed_at = (
            datetime.now(timezone.utc)
            .isoformat(timespec="seconds")
            .replace("+00:00", "Z")
        )

        label = binding.target.label or binding.target.kind
        evidence: dict[str, object] = {
            "ref": f"ev_obs_{sequence:04d}",
            "source": spec.evidence_source,
            "observed_at": observed_at,
            "world_revision": world_revision,
            "scope": f"{binding.target.kind}:{label}"[:512],
            "confidence": (
                float(result.confidence)
                if result.confidence is not None
                else None
            ),
            "content": evidence_content,
            "limitations": list(result.limitations),
        }
        return evidence

    def revoke_task(self, task_id: str) -> None:
        """Invalidate all refs and evidence sequence state for a completed task."""
        self._bindings = {
            key: value
            for key, value in self._bindings.items()
            if value.task_id != task_id
        }
        self._evidence_sequences.pop(task_id, None)

    def clear(self) -> None:
        """Drop all local capability bindings and task evidence counters."""
        self._bindings.clear()
        self._evidence_sequences.clear()
