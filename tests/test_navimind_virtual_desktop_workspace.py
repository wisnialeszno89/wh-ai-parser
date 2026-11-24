"""Linux Codespaces tests for human interruption of a simulated WindowHub mission."""
from app.agent.offers.windowhub_commercial_quote_routes import (
    QuoteCapabilities, QuoteRequest, TechnicalFinding, TechnicalStatus,
)
from app.agent.runtime.navimind_mission_coordinator import PositionTask
from app.agent.runtime.navimind_virtual_windowhub import (
    VirtualPosition, VirtualWindowHub,
)
from app.agent.runtime.navimind_virtual_desktop_workspace import (
    PinnedMissionSession, SessionStatus, VirtualDesktopWorkspace,
)


def caps():
    return QuoteCapabilities(
        exact_catalogue_construction_verified=False,
        description_field_verified=True,
        descriptive_position_supported=True,
        placeholder_position_supported=True,
        image_insert_supported=True,
        manual_price_field_verified=True,
        available_placeholder_width_mm=1000,
        available_placeholder_height_mm=1000,
    )


def task(index="1", *, image=False):
    return PositionTask(
        index,
        QuoteRequest(
            "Oferta konstrukcji nietypowej", quantity=1,
            requested_width_mm=2300, requested_height_mm=2700,
            manual_unit_price="3500.00",
            image_reference="fixture.png" if image else None,
            image_use_authorized=image,
        ),
        TechnicalFinding(TechnicalStatus.NOT_CHECKED, "Weryfikacja techniczna"),
    )


def setup(*, image=False):
    target = VirtualWindowHub("OFR/OURS", caps())
    other = VirtualWindowHub("OFR/OTHER", caps())
    workspace = VirtualDesktopWorkspace(
        {"OFR/OURS": target, "OFR/OTHER": other},
        foreground_document="OFR/OURS",
    )
    session = PinnedMissionSession("OFR/OURS", (task(image=image),))
    return workspace, session, target, other


def finish(workspace, session, limit=20):
    for _ in range(limit):
        event = session.step(workspace)
        if event.status in (SessionStatus.COMPLETE, SessionStatus.REVIEW, SessionStatus.PAUSED):
            return event
    raise AssertionError("virtual mission did not settle")


def test_complete_mission_stays_unsaved_and_requires_production_review():
    workspace, session, target, other = setup(image=True)
    outcome = finish(workspace, session)
    assert outcome.status == SessionStatus.COMPLETE
    assert session.report(workspace)["verified"]
    assert target.positions["1"].image_reference == "fixture.png"
    assert "gwaranc" not in target.positions["1"].description.casefold() or not target.saved
    assert target.positions["1"].unit_price == "3500.00"
    assert not target.saved and not target.sent
    assert other.positions == {}
    assert not session.report(workspace)["agent_authorized_to_save"]
    assert not session.report(workspace)["production_approval"]


def test_switching_to_other_offer_suspends_mission_without_mutating_other_offer():
    workspace, session, target, other = setup()
    first = session.step(workspace)
    assert first.action == "create_position"
    workspace.select_document("OFR/OTHER")
    before = dict(other.positions)
    paused = session.step(workspace)
    assert paused.status == SessionStatus.PAUSED
    assert paused.reason == "foreground_offer_changed"
    assert other.positions == before
    assert session.report(workspace)["status"] == "paused_not_current"
    workspace.select_document("OFR/OURS")
    completed = finish(workspace, session)
    assert completed.status == SessionStatus.COMPLETE
    assert len(target.positions) == 1
    assert other.positions == {}
    assert target.attempted_actions.count(("1", "create_position")) == 1


def test_wrong_application_pauses_without_editing():
    workspace, session, target, other = setup()
    target.observed_application = "notepad"
    result = session.step(workspace)
    assert result.status == SessionStatus.PAUSED
    assert target.positions == {}
    assert other.positions == {}


def test_stale_observation_pauses_until_new_scene():
    workspace, session, target, _ = setup()
    target.stale = True
    assert session.step(workspace).status == SessionStatus.PAUSED
    target.stale = False
    assert finish(workspace, session).status == SessionStatus.COMPLETE


def test_hand_edited_price_is_not_overwritten_by_old_agent_price():
    workspace, session, target, _ = setup()
    assert finish(workspace, session).status == SessionStatus.COMPLETE
    target.positions["1"].unit_price = "5.00"
    action = session.step(workspace)
    assert action.status == SessionStatus.REVIEW
    assert action.reason == "external_operator_edit_requires_review"
    assert target.positions["1"].unit_price == "5.00"
    assert not target.saved


def test_human_modified_description_is_preserved_for_operator_review():
    workspace, session, target, _ = setup()
    assert finish(workspace, session).status == SessionStatus.COMPLETE
    target.positions["1"].description = "Ręczna korekta handlowca"
    target.active_position_id = None
    first = session.step(workspace)
    assert first.reason == "external_operator_edit_requires_review"
    assert first.status == SessionStatus.REVIEW
    target.activate("1")
    second = session.step(workspace)
    assert second.status == SessionStatus.REVIEW
    assert target.positions["1"].description == "Ręczna korekta handlowca"


def test_switching_active_position_protects_other_item():
    from app.agent.offers.windowhub_commercial_quote_routes import plan_commercial_quote
    workspace, session, target, _ = setup()
    task = session.tasks[0]
    plan = plan_commercial_quote(task.request, target.capabilities, task.technical)
    target.positions["1"] = VirtualPosition(route=plan.route.value,
                                            description=plan.proposed_description)
    target.positions["2"] = VirtualPosition(route="text_only",
                                            description="Do not edit", unit_price="999")
    target.active_position_id = "2"
    event = session.step(workspace)
    assert event.action == "activate_position"
    assert target.active_position_id == "1"
    event = session.step(workspace)
    assert event.action == "set_manual_price"
    assert target.positions["2"].description == "Do not edit"
    assert target.positions["2"].unit_price == "999"


def test_human_created_valid_position_is_not_duplicated():
    from app.agent.offers.windowhub_commercial_quote_routes import plan_commercial_quote
    workspace, session, target, _ = setup()
    item = session.tasks[0]
    route = plan_commercial_quote(item.request, target.capabilities, item.technical).route.value
    target.positions["1"] = VirtualPosition(route=route)
    target.active_position_id = "1"
    assert finish(workspace, session).status == SessionStatus.COMPLETE
    assert len(target.positions) == 1
    assert ("1", "create_position") not in target.attempted_actions


def test_noop_creation_is_not_repeated_after_resuming():
    workspace, session, target, _ = setup()
    target.injected_noops.add(("1", "create_position"))
    event = session.step(workspace)
    assert event.status == SessionStatus.REVIEW
    assert target.attempted_actions == [("1", "create_position")]
    workspace.select_document("OFR/OTHER")
    assert session.step(workspace).status == SessionStatus.PAUSED
    workspace.select_document("OFR/OURS")
    event = session.step(workspace)
    assert event.status == SessionStatus.REVIEW
    assert "action_repeated_without_progress" in event.reason
    assert target.attempted_actions == [("1", "create_position")]


def test_customer_offer_identity_never_inferred_from_a_second_document():
    workspace, session, target, other = setup()
    workspace.select_document("OFR/OTHER")
    other.positions["1"] = VirtualPosition(route="descriptive_placeholder",
                                            description="Other customer's window",
                                            unit_price="3500.00")
    result = session.step(workspace)
    assert result.status == SessionStatus.PAUSED
    assert result.verified_position_count == 0
    assert target.positions == {}


def test_missing_foreground_pauses_safely():
    workspace, session, target, _ = setup()
    workspace.select_document(None)
    event = session.step(workspace)
    assert event.status == SessionStatus.PAUSED
    assert not session.report(workspace)["verified"]
    assert target.positions == {}


def test_operator_deleted_position_requires_review_not_silent_recreation():
    workspace, session, target, _ = setup()
    assert finish(workspace, session).status == SessionStatus.COMPLETE
    del target.positions["1"]
    result = session.step(workspace)
    assert result.status == SessionStatus.REVIEW
    assert result.reason == "external_operator_edit_requires_review"
    assert target.positions == {}
    assert target.attempted_actions.count(("1", "create_position")) == 1


def test_operator_edits_while_other_offer_active_are_detected_on_return():
    workspace, session, target, other = setup()
    assert finish(workspace, session).status == SessionStatus.COMPLETE
    workspace.select_document("OFR/OTHER")
    assert session.step(workspace).status == SessionStatus.PAUSED
    target.positions["1"].unit_price = "3200.00"
    workspace.select_document("OFR/OURS")
    event = session.step(workspace)
    assert event.status == SessionStatus.REVIEW
    assert target.positions["1"].unit_price == "3200.00"
    assert other.positions == {}
