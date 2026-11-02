from app.agent.bridge.agent_task_contract_v2 import (
    validate_agent_task_v2_payload,
)
from app.agent.bridge.agent_task_v2_world_builder import (
    AgentTaskV2WorldBuilder,
)
from app.agent.perception.screen_element import ScreenElement
from app.agent.runtime.read_only_observation_broker import (
    ObservationCapabilitySpec,
    ObservationReadResult,
    ObservationRejected,
    ReadOnlyObservationBroker,
)


def make_snapshot():
    scene = type("Scene", (), {"observation": type("Observation", (), {
        "state": type("State", (), {
            "active_application": "WindowHub",
            "active_window_title": "Nowa oferta",
        })()
    })(), "elements": (
        ScreenElement(kind="table", label="Lista klientów"),
    )})()
    return AgentTaskV2WorldBuilder().build(
        scene,
        task_id="task-001",
        world_revision=9,
        observed_at="2026-11-02T06:00:00Z",
    )


def table_spec(classification="ui_structure"):
    return ObservationCapabilitySpec(
        name="read_table_page",
        description="Read one bounded page from a semantic table.",
        input_contract="table_page_v1",
        max_items=10,
        data_classification=classification,
        evidence_source="uia_grid",
        timeout_seconds=2.0,
        max_result_bytes=8_192,
    )


def table_reader(target, parameters, context):
    assert target.label == "Lista klientów"
    assert parameters["limit"] <= context.max_items
    return ObservationReadResult(
        content={
            "headers": ["Kolumna 1", "Kolumna 2"],
            "rows": [["A", "1"], ["B", "2"]],
            "offset": parameters["offset"],
            "has_more": True,
            "reported_row_count": 6818,
        },
        limitations=("Provider-reported row count is not confirmed record count.",),
        confidence=0.99,
    )


def make_bound_broker(classification="ui_structure", authorized=None):
    broker = ReadOnlyObservationBroker(
        authorized_data_classifications=(
            frozenset({"ui_structure"})
            if authorized is None
            else frozenset(authorized)
        )
    )
    broker.register(table_spec(classification), table_reader)
    snapshot = make_snapshot()
    descriptor = broker.bind(
        snapshot,
        capability_name="read_table_page",
        target_ref="ent_0001",
    )
    request = {
        "capability_id": descriptor["id"],
        "target_ref": "ent_0001",
        "parameters": {"offset": 0, "limit": 5},
        "based_on_world_revision": 9,
    }
    return broker, descriptor, request


def test_broker_exposes_only_registered_read_only_capability():
    broker, descriptor, _ = make_bound_broker()

    assert descriptor == {
        "id": "obs_0001",
        "description": "Read one bounded page from a semantic table.",
        "target_ref": "ent_0001",
        "input_contract": "table_page_v1",
        "max_items": 10,
        "data_classification": "ui_structure",
        "read_only": True,
    }


def test_broker_returns_bounded_table_content_as_evidence():
    broker, _, request = make_bound_broker()

    evidence = broker.observe(
        request,
        task_id="task-001",
        world_revision=9,
        max_observation_items=5,
        max_evidence_bytes=8_192,
    )

    assert evidence["ref"] == "ev_obs_0001"
    assert evidence["source"] == "uia_grid"
    assert evidence["world_revision"] == 9
    assert evidence["content"]["headers"] == ["Kolumna 1", "Kolumna 2"]
    assert evidence["content"]["rows"] == [["A", "1"], ["B", "2"]]
    assert "not confirmed record count" in evidence["limitations"][0]


def test_broker_fails_closed_for_business_records_without_permission():
    broker, _, request = make_bound_broker("business_records")

    try:
        broker.observe(
            request,
            task_id="task-001",
            world_revision=9,
            max_observation_items=5,
            max_evidence_bytes=8_192,
        )
    except ObservationRejected as exc:
        assert "data_classification_not_authorized" in str(exc)
    else:
        raise AssertionError("Business-record observation was not blocked.")


def test_broker_allows_business_records_only_with_explicit_local_permission():
    broker, _, request = make_bound_broker(
        "business_records",
        authorized={"ui_structure", "business_records"},
    )

    evidence = broker.observe(
        request,
        task_id="task-001",
        world_revision=9,
        max_observation_items=5,
        max_evidence_bytes=8_192,
    )
    assert evidence["content"]["rows"][0] == ["A", "1"]


def test_broker_rejects_unknown_capability_and_mismatched_target():
    broker, _, request = make_bound_broker()
    request["capability_id"] = "obs_not_exposed"

    try:
        broker.observe(
            request,
            task_id="task-001",
            world_revision=9,
            max_observation_items=5,
            max_evidence_bytes=8_192,
        )
    except ObservationRejected as exc:
        assert "capability_not_exposed" in str(exc)
    else:
        raise AssertionError("Unknown capability was accepted.")

    broker, _, request = make_bound_broker()
    request["target_ref"] = "ent_9999"
    try:
        broker.observe(
            request,
            task_id="task-001",
            world_revision=9,
            max_observation_items=5,
            max_evidence_bytes=8_192,
        )
    except ObservationRejected as exc:
        assert "target_ref_mismatch" in str(exc)
    else:
        raise AssertionError("Mismatched target was accepted.")


def test_broker_rejects_stale_task_and_world_revision():
    broker, _, request = make_bound_broker()

    for task_id, revision, expected in (
        ("other-task", 9, "task_scope_mismatch"),
        ("task-001", 10, "binding_stale"),
    ):
        try:
            broker.observe(
                request,
                task_id=task_id,
                world_revision=revision,
                max_observation_items=5,
                max_evidence_bytes=8_192,
            )
        except ObservationRejected as exc:
            assert expected in str(exc)
        else:
            raise AssertionError(f"Expected rejection: {expected}")


def test_broker_rejects_out_of_bounds_and_untyped_table_requests():
    broker, _, request = make_bound_broker()
    request["parameters"]["limit"] = 11

    try:
        broker.observe(
            request,
            task_id="task-001",
            world_revision=9,
            max_observation_items=20,
            max_evidence_bytes=8_192,
        )
    except ObservationRejected as exc:
        assert "limit_out_of_bounds" in str(exc)
    else:
        raise AssertionError("Oversized page was accepted.")

    broker, _, request = make_bound_broker()
    request["parameters"]["selector"] = "arbitrary UIA selector"

    try:
        broker.observe(
            request,
            task_id="task-001",
            world_revision=9,
            max_observation_items=20,
            max_evidence_bytes=8_192,
        )
    except ObservationRejected as exc:
        assert "table_page_parameters_invalid" in str(exc)
    else:
        raise AssertionError("Arbitrary selector was accepted.")


def test_broker_rejects_oversized_nested_result_lists():
    broker = ReadOnlyObservationBroker()
    broker.register(
        table_spec(),
        lambda target, parameters, context: ObservationReadResult(
            content={
                "headers": ["Name"],
                "rows": [["x"] * 2000],
                "offset": 0,
                "has_more": False,
            }
        ),
    )
    descriptor = broker.bind(
        make_snapshot(),
        capability_name="read_table_page",
        target_ref="ent_0001",
    )
    request = {
        "capability_id": descriptor["id"],
        "target_ref": "ent_0001",
        "parameters": {"offset": 0, "limit": 5},
        "based_on_world_revision": 9,
    }

    try:
        broker.observe(
            request,
            task_id="task-001",
            world_revision=9,
            max_observation_items=5,
            max_evidence_bytes=8_192,
        )
    except ObservationRejected as exc:
        assert "result_list_too_large" in str(exc)
    else:
        raise AssertionError("Oversized nested result list was accepted.")


def test_broker_rejects_table_rows_with_mismatched_cell_count():
    broker = ReadOnlyObservationBroker()
    broker.register(
        table_spec(),
        lambda target, parameters, context: ObservationReadResult(
            content={
                "headers": ["Name"],
                "rows": [["A", "unexpected extra cell"]],
                "offset": 0,
                "has_more": False,
            }
        ),
    )
    descriptor = broker.bind(
        make_snapshot(),
        capability_name="read_table_page",
        target_ref="ent_0001",
    )

    try:
        broker.observe(
            {
                "capability_id": descriptor["id"],
                "target_ref": "ent_0001",
                "parameters": {"offset": 0, "limit": 1},
                "based_on_world_revision": 9,
            },
            task_id="task-001",
            world_revision=9,
            max_observation_items=5,
            max_evidence_bytes=8_192,
        )
    except ObservationRejected as exc:
        assert "table_page_row_shape_invalid" in str(exc)
    else:
        raise AssertionError("Table row with mismatched cell count was accepted.")


def test_broker_rejects_provider_identifiers_in_returned_evidence():
    broker = ReadOnlyObservationBroker()
    broker.register(
        table_spec(),
        lambda target, parameters, context: ObservationReadResult(
            content={
                "headers": ["Name"],
                "rows": [["A"]],
                "offset": 0,
                "has_more": False,
                "runtime_id": "[7,123]",
            }
        ),
    )
    descriptor = broker.bind(
        make_snapshot(),
        capability_name="read_table_page",
        target_ref="ent_0001",
    )

    try:
        broker.observe(
            {
                "capability_id": descriptor["id"],
                "target_ref": "ent_0001",
                "parameters": {"offset": 0, "limit": 1},
                "based_on_world_revision": 9,
            },
            task_id="task-001",
            world_revision=9,
            max_observation_items=5,
            max_evidence_bytes=8_192,
        )
    except ObservationRejected as exc:
        assert "provider_field" in str(exc)
    else:
        raise AssertionError("Provider identifier crossed the broker boundary.")


def test_broker_generates_task_local_evidence_refs_and_revokes_bindings():
    broker, _, request = make_bound_broker()

    first = broker.observe(
        request,
        task_id="task-001",
        world_revision=9,
        max_observation_items=5,
        max_evidence_bytes=8_192,
    )
    second = broker.observe(
        request,
        task_id="task-001",
        world_revision=9,
        max_observation_items=5,
        max_evidence_bytes=8_192,
    )
    assert first["ref"] == "ev_obs_0001"
    assert second["ref"] == "ev_obs_0002"

    broker.revoke_task("task-001")
    try:
        broker.observe(
            request,
            task_id="task-001",
            world_revision=9,
            max_observation_items=5,
            max_evidence_bytes=8_192,
        )
    except ObservationRejected as exc:
        assert "capability_not_exposed" in str(exc)
    else:
        raise AssertionError("Revoked capability was accepted.")



def test_broker_descriptor_fits_the_v2_request_contract():
    broker, descriptor, _ = make_bound_broker()
    snapshot = make_snapshot()
    request = {
        "version": "2",
        "task_id": "task-001",
        "goal": "Inspect the visible table structure.",
        "intent": "computer_use",
        "session_id": None,
        "task_state": {
            "cycle": 1,
            "max_cycles": 20,
            "reasoning_calls_remaining": 5,
        },
        "world": dict(snapshot.payload),
        "capabilities": {
            "observations": [descriptor],
            "actions": [],
        },
        "knowledge": None,
        "experience": [],
        "constraints": {
            "max_observations_per_cycle": 1,
            "max_observation_items": 10,
            "max_evidence_bytes": 8_192,
            "semantic_only": True,
            "verify_each_action": True,
        },
        "metadata": {},
    }

    validate_agent_task_v2_payload(request)


def test_broker_does_not_call_reader_when_classification_is_blocked():
    calls = []
    broker = ReadOnlyObservationBroker()
    broker.register(
        table_spec("business_records"),
        lambda target, parameters, context: (
            calls.append("called")
            or table_reader(target, parameters, context)
        ),
    )
    descriptor = broker.bind(
        make_snapshot(),
        capability_name="read_table_page",
        target_ref="ent_0001",
    )
    request = {
        "capability_id": descriptor["id"],
        "target_ref": "ent_0001",
        "parameters": {"offset": 0, "limit": 5},
        "based_on_world_revision": 9,
    }

    try:
        broker.observe(
            request,
            task_id="task-001",
            world_revision=9,
            max_observation_items=5,
            max_evidence_bytes=8_192,
        )
    except ObservationRejected as exc:
        assert "data_classification_not_authorized" in str(exc)
    else:
        raise AssertionError("Unauthorized observation was accepted.")

    assert calls == []


def test_broker_rejects_result_exceeding_byte_budget():
    broker = ReadOnlyObservationBroker()
    spec = ObservationCapabilitySpec(
        name="read_table_page",
        description="Read one bounded page from a semantic table.",
        input_contract="table_page_v1",
        max_items=10,
        data_classification="ui_structure",
        evidence_source="uia_grid",
        max_result_bytes=1_024,
    )
    broker.register(
        spec,
        lambda target, parameters, context: ObservationReadResult(
            content={
                "headers": ["Name"],
                "rows": [["z" * 900] for _ in range(5)],
                "offset": 0,
                "has_more": False,
            }
        ),
    )
    descriptor = broker.bind(
        make_snapshot(),
        capability_name="read_table_page",
        target_ref="ent_0001",
    )

    try:
        broker.observe(
            {
                "capability_id": descriptor["id"],
                "target_ref": "ent_0001",
                "parameters": {"offset": 0, "limit": 5},
                "based_on_world_revision": 9,
            },
            task_id="task-001",
            world_revision=9,
            max_observation_items=5,
            max_evidence_bytes=1_024,
        )
    except ObservationRejected as exc:
        assert "byte_budget_exceeded" in str(exc)
    else:
        raise AssertionError("Oversized evidence payload was accepted.")


def test_broker_rejects_a_handler_that_returns_after_its_deadline():
    now = [0.0]

    def clock():
        return now[0]

    def slow_reader(target, parameters, context):
        now[0] = context.deadline_monotonic + 0.1
        return ObservationReadResult(
            content={
                "headers": ["Name"],
                "rows": [["A"]],
                "offset": 0,
                "has_more": False,
            }
        )

    broker = ReadOnlyObservationBroker(clock=clock)
    broker.register(table_spec(), slow_reader)
    descriptor = broker.bind(
        make_snapshot(),
        capability_name="read_table_page",
        target_ref="ent_0001",
    )

    try:
        broker.observe(
            {
                "capability_id": descriptor["id"],
                "target_ref": "ent_0001",
                "parameters": {"offset": 0, "limit": 1},
                "based_on_world_revision": 9,
            },
            task_id="task-001",
            world_revision=9,
            max_observation_items=5,
            max_evidence_bytes=8_192,
        )
    except ObservationRejected as exc:
        assert "time_budget_exceeded" in str(exc)
    else:
        raise AssertionError("Late observation result was accepted.")


def test_broker_rejects_boolean_as_world_revision():
    broker, _, request = make_bound_broker()
    request["based_on_world_revision"] = True

    try:
        broker.observe(
            request,
            task_id="task-001",
            world_revision=9,
            max_observation_items=5,
            max_evidence_bytes=8_192,
        )
    except ObservationRejected as exc:
        assert "invalid_based_on_world_revision" in str(exc)
    else:
        raise AssertionError("Boolean revision was accepted.")
