"""End-to-end in-memory mission tests, portable to GitHub Codespaces."""
from app.agent.offers.windowhub_commercial_quote_routes import (
    QuoteCapabilities, QuoteRequest, TechnicalFinding, TechnicalStatus,
)
from app.agent.runtime.navimind_mission_coordinator import PositionTask
from app.agent.runtime.navimind_virtual_windowhub import (
    VirtualPosition, VirtualWindowHub, run_virtual_mission,
)


def capabilities(**changes):
    params = dict(
        exact_catalogue_construction_verified=False,
        description_field_verified=True,
        descriptive_position_supported=True,
        placeholder_position_supported=True,
        image_insert_supported=True,
        manual_price_field_verified=True,
        available_placeholder_width_mm=1000,
        available_placeholder_height_mm=1000,
    )
    params.update(changes)
    return QuoteCapabilities(**params)


def position(identifier="1", **changes):
    params = dict(
        description="Niestandardowe okno z opisem",
        quantity=1, requested_width_mm=2300,
        requested_height_mm=2700, manual_unit_price="3450.00",
    )
    params.update(changes)
    return PositionTask(
        identifier, QuoteRequest(**params),
        TechnicalFinding(TechnicalStatus.KNOWN_OUTSIDE_WARRANTY,
                         "Przekroczony zakres gwarancyjny", "manual:example"),
    )


def test_full_quotation_two_positions_with_image_and_manual_price():
    tasks = (
        position("1", image_reference="image-a.png", image_use_authorized=True),
        position("2", manual_unit_price="850.00"),
    )
    env = VirtualWindowHub("OFR/TEST", capabilities())
    trace = run_virtual_mission(tasks, env)
    assert trace.finished
    assert all(p["quotation_position_complete"] for p in trace.summary["positions"])
    assert len(env.positions) == 2
    assert env.positions["1"].image_reference == "image-a.png"
    assert env.positions["1"].unit_price == "3450.00"
    assert env.positions["2"].unit_price == "850.00"
    assert "wymiary" not in env.positions["1"].description.casefold() or "2300 x 2700" in env.positions["1"].description
    assert "gwaranc" in env.positions["1"].description.casefold()
    assert not env.saved and not env.sent
    assert not trace.summary["agent_authorized_to_save"]


def test_empty_first_position_is_not_duplicated_after_verified_creation():
    env = VirtualWindowHub("OFR/TEST", capabilities())
    tasks = (position(),)
    outcome = run_virtual_mission(tasks, env)
    assert outcome.finished
    assert len([a for a in env.attempted_actions if a == ("1", "create_position")]) == 1


def test_noop_on_creation_escalates_and_does_not_blind_retry():
    env = VirtualWindowHub(
        "OFR/TEST", capabilities(),
        injected_noops={("1", "create_position")},
    )
    trace = run_virtual_mission((position(),), env)
    assert not trace.finished
    assert "action_repeated_without_progress" in trace.terminal_reason
    assert env.positions == {}
    assert env.attempted_actions == [("1", "create_position")]


def test_failure_during_description_stops_without_claiming_completion():
    env = VirtualWindowHub(
        "OFR/TEST", capabilities(),
        injected_noops={("1", "write_description")},
    )
    trace = run_virtual_mission((position(),), env)
    assert not trace.finished
    assert env.positions["1"].description is None
    assert not trace.summary["all_position_requirements_verified"]


def test_wrong_application_or_stale_scene_cannot_execute():
    tasks = (position(),)
    env = VirtualWindowHub("OFR/TEST", capabilities(), observed_application="notepad")
    trace = run_virtual_mission(tasks, env)
    assert not trace.finished
    assert env.positions == {}
    env2 = VirtualWindowHub("OFR/TEST", capabilities(), stale=True)
    assert not run_virtual_mission(tasks, env2).finished


def test_unknown_image_capability_requires_review():
    item = position(image_reference="photo.jpg", image_use_authorized=True)
    env = VirtualWindowHub("OFR/TEST", capabilities(image_insert_supported=False))
    trace = run_virtual_mission((item,), env)
    assert not trace.finished
    assert "image_requirements_unresolved" in trace.terminal_reason
    assert env.positions["1"].description is not None


def test_missing_price_is_not_fabricated():
    item = position(manual_unit_price=None)
    env = VirtualWindowHub("OFR/TEST", capabilities())
    trace = run_virtual_mission((item,), env)
    assert not trace.finished
    assert env.positions["1"].unit_price is None
    assert "price" in trace.terminal_reason


def test_manual_price_field_unavailable_requires_review():
    item = position()
    env = VirtualWindowHub("OFR/TEST", capabilities(manual_price_field_verified=False))
    trace = run_virtual_mission((item,), env)
    assert not trace.finished
    assert env.positions == {}


def test_wrong_document_readback_never_counts():
    tasks = (position(),)
    env = VirtualWindowHub("OFR/TEST", capabilities())
    env.positions["1"] = VirtualPosition(route="descriptive_placeholder")
    env.active_position_id = "1"
    original = env.observe(tasks)
    assert original[0].created_verified
    env.document_id = "OFR/OTHER"
    assert not any(r.document_id == "OFR/TEST" for r in env.observe(tasks))
    assert not run_virtual_mission(tasks, env).summary["agent_authorized_to_send"]


def test_stray_action_and_price_tampering_are_rejected():
    from app.agent.runtime.navimind_mission_coordinator import MissionAction, MissionIntent
    tasks = (position(),)
    env = VirtualWindowHub("OFR/TEST", capabilities())
    assert not env.apply(MissionIntent(
        action=MissionAction.SET_MANUAL_PRICE, position_id="1",
        reason="try", price="999999.00", requires_v2_executor=True,
    ), tasks)
    assert not env.apply(MissionIntent(
        action=MissionAction.CREATE_POSITION, position_id="42",
        reason="wrong customer", requires_v2_executor=True,
    ), tasks)
    assert env.positions == {}


def test_max_cycles_is_bounded():
    env = VirtualWindowHub("OFR/TEST", capabilities())
    result = run_virtual_mission((position(),), env, max_cycles=1)
    assert not result.finished
    assert result.terminal_reason == "max_cycles_exhausted"



def test_missing_image_must_never_verify_when_image_and_plan_are_both_none():
    item = position(image_reference="required-photo.png", image_use_authorized=True)
    env = VirtualWindowHub("OFR/TEST", capabilities(image_insert_supported=False))
    env.positions["1"] = VirtualPosition(
        route="descriptive_placeholder", description="Opis próbny",
        image_reference=None, unit_price="3450.00",
    )
    proof = env.observe((item,))[0]
    assert proof.image_verified is False
    assert not run_virtual_mission((item,), env).finished


def test_image_without_user_permission_is_not_verified_by_empty_values():
    item = position(image_reference="restricted.png", image_use_authorized=False)
    env = VirtualWindowHub("OFR/TEST", capabilities())
    env.positions["1"] = VirtualPosition(route="descriptive_placeholder")
    assert env.observe((item,))[0].image_verified is False
    result = run_virtual_mission((item,), env)
    assert not result.finished
    assert "image_requirements_unresolved" in result.terminal_reason
