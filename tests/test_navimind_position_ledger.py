"""Offline large customer enquiries: no Windows input, model or API calls."""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.agent.runtime.navimind_position_ledger import (
    PositionCheckpoint, PositionLedger, build_position_manifest,
    position_prompt, validate_bound_position_entry,
)
from app.agent.runtime.navimind_enquiry_inbox import LocalEnquiryInbox, EnquirySource
from app.agent.runtime.navimind_work_mission import (
    WorkMissionCoordinator, WorkStage,
)
from app.agent.runtime.navimind_local_input_arbiter import LocalInputArbiter
from app.agent.runtime.navimind_mission_chat import MissionChat
from app.agent.runtime.navimind_live_conversation import LiveMissionConversation


def inbox_with(*sources):
    inbox = LocalEnquiryInbox()
    inbox.set_text(sources[0])
    for index, body in enumerate(sources[1:], 1):
        inbox._sources.append(EnquirySource(
            f"customer-secret-{index}.pdf", "pdf", body,
            2, False, False,
        ))
    return inbox


def test_repeated_sizes_are_distinct_stable_source_positions_and_not_deduplicated():
    inbox = inbox_with(
        "2 Stk Fenster 1500x1400\n1 Stk Fenster 1500x1400",
        "3 Stk Fenster 1200x1000",
    )
    manifest = build_position_manifest(inbox)
    assert manifest.safe_to_sequence
    assert len(manifest.positions) == 3
    assert [p.position_id for p in manifest.positions] == [
        "S01-P001", "S01-P002", "S02-P001",
    ]
    assert [p.quantity for p in manifest.positions] == [2, 1, 3]
    assert manifest.positions[0].source_fingerprint != manifest.positions[1].source_fingerprint
    assert "customer-secret" not in repr(manifest)


def test_large_multi_source_input_has_all_position_ids_and_scoped_prompts():
    source_a = "\n".join(
        f"1 Stk Fenster {1000 + i * 10}x1400" for i in range(26)
    )
    source_b = "\n".join(
        f"2 Stk Fenster {1600 + i * 10}x1500" for i in range(24)
    )
    manifest = build_position_manifest(inbox_with(source_a, source_b))
    assert len(manifest.positions) == 50
    assert manifest.safe_to_sequence
    ledger = PositionLedger(manifest)
    assert ledger.active.position_id == "S01-P001"
    first_prompt = position_prompt(ledger.active, index=0, total=50)
    assert "1000" in first_prompt
    assert "1010" not in first_prompt
    assert "S01-P001" in first_prompt
    assert "1/50" in first_prompt


def test_scoped_value_guard_never_borrows_size_or_quantity_from_next_position():
    manifest = build_position_manifest(
        inbox_with("2 Stk Fenster 1500x1400\n3 Stk Fenster 1300x1200")
    )
    first, second = manifest.positions
    assert validate_bound_position_entry(
        first, field_name="width_1", proposed_value="1500",
    )[0]
    assert not validate_bound_position_entry(
        first, field_name="width_1", proposed_value="1300",
    )[0]
    assert not validate_bound_position_entry(
        first, field_name="quantity_input", proposed_value="3",
    )[0]
    assert validate_bound_position_entry(
        second, field_name="quantity_input", proposed_value="3",
    )[0]
    assert not validate_bound_position_entry(
        first, field_name="description_input", proposed_value="HST",
    )[0]


def test_partial_scan_and_unparsed_pdf_block_sequence_without_silent_skipping():
    inbox = inbox_with("1 Stk Fenster 1500x1400")
    inbox._sources.append(EnquirySource(
        "scan-secret.pdf", "pdf", "", 5, False, True,
    ))
    manifest = build_position_manifest(inbox)
    assert len(manifest.positions) == 1
    assert manifest.incomplete_sources
    assert manifest.unparsed_sources
    assert not manifest.safe_to_sequence


def test_missing_quantity_and_conflicting_dimensions_cannot_be_filled_by_guess():
    manifest = build_position_manifest(
        inbox_with("Fenster 1500x1400\nFenster 1500x1400\n1300x1200")
    )
    assert len(manifest.positions) == 2
    assert not manifest.positions[0].ready_for_geometry
    assert not manifest.positions[1].ready_for_geometry
    assert not validate_bound_position_entry(
        manifest.positions[0], field_name="quantity_input",
        proposed_value="1",
    )[0]


def test_ledger_rejects_model_completion_and_wrong_position_or_document():
    manifest = build_position_manifest(
        inbox_with("2 Stk Fenster 1500x1400\n1 Stk Fenster 1300x1200")
    )
    ledger = PositionLedger(manifest)
    first = manifest.positions[0]
    checkpoint = PositionCheckpoint(
        first.position_id, "OFR/101", 1500, 1400, 2,
        independent_readback=True, construction_verified=True,
        signature="uia:exact-window:unique-readback",
    )
    invalid = [
        PositionCheckpoint(
            first.position_id, "OFR/OTHER", 1500, 1400, 2,
            True, True, "proof",
        ),
        PositionCheckpoint(
            "S01-P002", "OFR/101", 1500, 1400, 2,
            True, True, "proof",
        ),
        PositionCheckpoint(
            first.position_id, "OFR/101", 1500, 1400, 2,
            True, False, "proof",
        ),
        PositionCheckpoint(
            first.position_id, "OFR/101", 1500, 1400, 2,
            True, True, "",
        ),
    ]
    for other in invalid:
        with pytest.raises(ValueError):
            ledger.complete_verified(other, pinned_document="OFR/101")
    updated = ledger.complete_verified(checkpoint, pinned_document="OFR/101")
    assert updated.active.position_id == "S01-P002"
    assert len(updated.completed) == 1
    assert ledger.active.position_id == "S01-P001"
    with pytest.raises(ValueError):
        updated.complete_verified(checkpoint, pinned_document="OFR/101")


def test_consent_epoch_pins_multi_position_manifest_and_revocation_invalidates_mission():
    inbox = inbox_with(
        "2 Stk Fenster 1500x1400\n1 Stk Fenster 1200x1000"
    )
    manifest = build_position_manifest(inbox)
    chat = MissionChat(
        document_key="OFR/101", arbiter=LocalInputArbiter()
    )
    conversation = LiveMissionConversation(chat, None)
    conversation.approve_document_context(
        "Zatwierdzona analiza PDF", mission_evidence="PDF klienta",
        position_manifest=manifest,
    )
    chat.user_message("Utwórz dwie konstrukcje z PDF")
    coordinator = WorkMissionCoordinator(
        chat,
        document_snapshot_provider=conversation.document_access_snapshot,
        position_manifest_provider=conversation.position_manifest_snapshot,
    )
    mission = coordinator.queue_current()
    assert len(mission.position_ledger.manifest.positions) == 2
    assert coordinator.is_current(mission)
    inbox.set_text("1 Stk Fenster 3000x1000")
    assert coordinator.is_current(mission)
    conversation.revoke_document_context()
    assert not coordinator.is_current(mission)
    assert coordinator.transition(mission.task_id, WorkStage.READY) is None
    conversation.close()


def test_coordinator_rejects_unverified_next_position_and_accepts_trusted_readback():
    manifest = build_position_manifest(
        inbox_with("2 Stk Fenster 1500x1400\n1 Stk Fenster 1300x1200")
    )
    chat = MissionChat(document_key="OFR/101", arbiter=LocalInputArbiter())
    chat.user_message("Wprowadź okna")
    queue = WorkMissionCoordinator(
        chat, document_snapshot_provider=lambda: (1, "PDF"),
        position_manifest_provider=lambda: (1, manifest),
    )
    mission = queue.queue_current()
    queue.transition(mission.task_id, WorkStage.PAUSED)
    proof = PositionCheckpoint(
        "S01-P001", "OFR/101", 1500, 1400, 2, True, True,
        "native-readable-proof",
    )
    assert not queue.record_independent_position_readback(
        task_id=mission.task_id, checkpoint=proof,
        pinned_document="OFR/DIFFERENT",
    )
    assert queue.record_independent_position_readback(
        task_id=mission.task_id, checkpoint=proof,
        pinned_document="OFR/101",
    )
    assert queue.current().position_ledger.active.position_id == "S01-P002"
    assert queue.current().stage == WorkStage.READY


def test_v2_large_enquiry_prompt_contains_only_active_position_not_all_pdf_sizes():
    from app.agent.runtime.navimind_work_mission import scoped_v2_mission_goal
    from dataclasses import replace
    manifest = build_position_manifest(
        inbox_with(
            "2 Stk Fenster 1500x1400\n"
            "3 Stk Fenster 1300x1200\n"
            "1 Stk Fenster 1800x1700"
        )
    )
    chat = MissionChat(
        document_key="OFR/101", arbiter=LocalInputArbiter()
    )
    chat.user_message("Zrób ofertę według zatwierdzonego PDF.")
    queue = WorkMissionCoordinator(
        chat,
        document_snapshot_provider=lambda: (1, "1500x1400, 1300x1200, 1800x1700"),
        position_manifest_provider=lambda: (1, manifest),
    )
    mission = queue.queue_current()
    first = scoped_v2_mission_goal(mission)
    assert "S01-P001" in first
    assert "1500" in first and "1400" in first
    assert "1300" not in first and "1800" not in first
    next_ledger = replace(mission.position_ledger, active_index=1)
    second = scoped_v2_mission_goal(replace(mission, position_ledger=next_ledger))
    assert "S01-P002" in second
    assert "1300" in second and "1200" in second
    assert "1500" not in second and "1800" not in second


def test_verified_next_position_resets_step_budget_but_preserves_total_count():
    manifest = build_position_manifest(
        inbox_with("2 Stk Fenster 1500x1400\n1 Stk Fenster 1300x1200")
    )
    chat = MissionChat(document_key="OFR/101", arbiter=LocalInputArbiter())
    chat.user_message("Przygotuj ofertę.")
    coordinator = WorkMissionCoordinator(
        chat, max_cycles=2,
        document_snapshot_provider=lambda: (1, "PDF"),
        position_manifest_provider=lambda: (1, manifest),
    )
    mission = coordinator.queue_current()
    for index in range(2):
        updated = coordinator.transition(
            mission.task_id, WorkStage.PAUSED,
            count_step=True, signature=f"verified-{index}",
        )
        assert updated is not None
    assert updated.cycles == 2
    assert updated.total_verified_actions == 2
    assert coordinator.record_independent_position_readback(
        task_id=mission.task_id,
        checkpoint=PositionCheckpoint(
            "S01-P001", "OFR/101", 1500, 1400, 2,
            True, True, "independent-native-readback",
        ),
        pinned_document="OFR/101",
    )
    following = coordinator.current()
    assert following.cycles == 0
    assert following.total_verified_actions == 2
    assert following.position_ledger.active.position_id == "S01-P002"


def test_german_numbered_positions_are_not_lost_in_long_enquiries():
    text = (
        "Anfrage:\n"
        "Pos. 1: 2 Stk Fenster 1500x1400\n"
        "Pos. 2: 1 Stk Fenster 1300x1200\n"
        "3) 4 Stk Fenster 1100x1000\n"
    )
    manifest = build_position_manifest(inbox_with(text))
    assert manifest.safe_to_sequence
    assert [(p.width_mm, p.height_mm, p.quantity)
            for p in manifest.positions] == [
        (1500, 1400, 2), (1300, 1200, 1), (1100, 1000, 4),
    ]


def test_numbered_unparseable_row_invalidates_whole_automatic_sequence():
    text = (
        "Pos. 1: 2 Stk Fenster 1500x1400\n"
        "Pos. 2: Fenster bez czytelnych wymiarów\n"
    )
    manifest = build_position_manifest(inbox_with(text))
    assert len(manifest.positions) == 2
    assert not manifest.positions[1].ready_for_geometry
    assert not validate_bound_position_entry(
        manifest.positions[1], field_name="width_1",
        proposed_value="1500",
    )[0]


def test_field_receipts_are_position_scoped_reject_other_values_and_reset_after_checkpoint():
    from app.agent.runtime.navimind_work_mission import PositionFieldReceipt
    manifest = build_position_manifest(
        inbox_with("2 Stk Fenster 1500x1400\n1 Stk Fenster 1300x1200")
    )
    chat = MissionChat(document_key="OFR/101", arbiter=LocalInputArbiter())
    chat.user_message("Przygotuj ofertę.")
    coordinator = WorkMissionCoordinator(
        chat, max_cycles=20,
        document_snapshot_provider=lambda: (1, "PDF"),
        position_manifest_provider=lambda: (1, manifest),
    )
    mission = coordinator.queue_current()
    assert coordinator.transition(
        mission.task_id, WorkStage.PAUSED, count_step=True,
        field_receipt=PositionFieldReceipt(
            "S01-P002", "width_1", "1300", "wrong-position", "width-ui",
        ),
    ) is None
    assert coordinator.transition(
        mission.task_id, WorkStage.PAUSED, count_step=True,
        field_receipt=PositionFieldReceipt(
            "S01-P001", "width_1", "1300", "wrong-value", "width-ui",
        ),
    ) is None
    for field, value in [
        ("quantity_input", "2"),
        ("width_1", "1500"), ("height_1", "1400"),
    ]:
        updated = coordinator.transition(
            mission.task_id, WorkStage.PAUSED, count_step=True,
            signature=field,
            field_receipt=PositionFieldReceipt(
                "S01-P001", field, value, f"fresh-native-{field}", f"rid-{field}",
            ),
        )
        assert updated is not None
    assert {x.field_name for x in updated.field_receipts} == {
        "quantity_input", "width_1", "height_1",
    }
    assert coordinator.record_independent_position_readback(
        task_id=mission.task_id,
        checkpoint=PositionCheckpoint(
            "S01-P001", "OFR/101", 1500, 1400, 2,
            True, True, "separate-construction-proof",
        ),
        pinned_document="OFR/101",
    )
    after = coordinator.current()
    assert after.position_ledger.active.position_id == "S01-P002"
    assert after.field_receipts == ()
    assert after.total_verified_actions == 3


def test_description_can_be_copied_from_one_source_position_but_not_invented():
    manifest = build_position_manifest(
        inbox_with("2 Stk Fenster 1500x1400\n1 Stk Fenster 1300x1200")
    )
    first, second = manifest.positions
    assert validate_bound_position_entry(
        first, field_name="description_input",
        proposed_value="Fenster 1500x1400",
    )[0]
    assert not validate_bound_position_entry(
        first, field_name="description_input",
        proposed_value="Fenster 1300x1200",
    )[0]
    assert validate_bound_position_entry(
        second, field_name="description_input",
        proposed_value="Fenster 1300x1200",
    )[0]
    assert not validate_bound_position_entry(
        first, field_name="description_input",
        proposed_value="Premiumfenster mit Montage",
    )[0]


def test_two_window_powershell_gate_accepts_only_exact_separate_window_positions():
    from app.agent.runtime.navimind_position_ledger import (
        two_window_test_gate,
    )
    okay = inbox_with(
        "Pos. 1: 1 Stk Fenster 1500x1400\n"
        "Pos. 2: 1 Stk Fenster 1300x1200"
    )
    accepted, reason = two_window_test_gate(okay)
    assert accepted, reason
    assert not two_window_test_gate(inbox_with(
        "1 Stk Fenster 1500x1400"
    ))[0]
    assert not two_window_test_gate(inbox_with(
        "1 Stk Fenster 1500x1400\n"
        "1 Stk Fenster 1300x1200\n"
        "1 Stk Fenster 1000x1100"
    ))[0]


def test_two_window_powershell_gate_blocks_unreadable_pdf_and_unknown_quantity():
    from app.agent.runtime.navimind_position_ledger import (
        two_window_test_gate,
    )
    partial = inbox_with(
        "1 Stk Fenster 1500x1400\n1 Stk Fenster 1300x1200"
    )
    partial._sources.append(EnquirySource(
        "confidential.pdf", "pdf", "", 3, False, True,
    ))
    assert not two_window_test_gate(partial)[0]
    assert not two_window_test_gate(inbox_with(
        "Fenster 1500x1400\nFenster 1300x1200"
    ))[0]


def test_source_scoped_explicit_catalogue_requests_never_borrow_neighbour_values():
    manifest = build_position_manifest(inbox_with(
        "Pos. 1: 1 Stk Fenster 1500x1400\n"
        "Profil: Veka Perfectline\n"
        "Farbe innen: Weiss\n"
        "Farbe außen: Anthrazit\n"
        "Verglasung: 2-fach\n"
        "Beschlag: activPilot\n"
        "Pos. 2: 1 Stk Fenster 1300x1200\n"
        "Profil: Veka Softline 82\n"
        "Farbe innen: Weiss\n"
        "Farbe außen: Weiss\n"
        "Verglasung: 3-fach\n"
        "Beschlag: proPilot"
    ))
    assert manifest.safe_to_sequence
    assert len(manifest.positions) == 2
    first, second = manifest.positions
    assert dict(first.catalogue_requirements) == {
        "profile": "Veka Perfectline",
        "color_inside": "Weiss",
        "color_outside": "Anthrazit",
        "glazing": "2-fach",
        "hardware": "activPilot",
    }
    assert dict(second.catalogue_requirements)["profile"] == "Veka Softline 82"
    assert dict(second.catalogue_requirements)["glazing"] == "3-fach"
    assert "Veka Softline" not in position_prompt(first, index=0, total=2)
    assert "Veka Perfectline" not in position_prompt(second, index=1, total=2)


def test_conflicting_explicit_catalogue_colors_block_source_automaticity():
    manifest = build_position_manifest(inbox_with(
        "Pos. 1: 1 Stk Fenster 1500x1400\n"
        "Farbe außen: Anthrazit\n"
        "Farbe außen: Weiss\n"
        "Pos. 2: 1 Stk Fenster 1300x1200"
    ))
    assert len(manifest.positions) == 2
    assert not manifest.positions[0].ready_for_geometry
    assert "conflicting_catalogue_requirements" in manifest.positions[0].issues


def test_direct_human_chat_two_windows_can_be_source_without_pdf_consent():
    from app.agent.runtime.navimind_position_ledger import (
        direct_chat_position_manifest,
    )
    message = (
        "Przygotuj nową niezapisaną ofertę:\n"
        "Pos. 1: 1 Stk Fenster 1500x1400\n"
        "Profil: Veka Perfectline\n"
        "Pos. 2: 1 Stk Fenster 1300x1200\n"
        "Profil: Veka Softline 82"
    )
    manifest = direct_chat_position_manifest(message)
    assert manifest is not None
    assert manifest.safe_to_sequence
    assert len(manifest.positions) == 2
    assert [p.position_id for p in manifest.positions] == [
        "S01-P001", "S01-P002"
    ]
    assert dict(manifest.positions[0].catalogue_requirements)["profile"] == "Veka Perfectline"
    assert dict(manifest.positions[1].catalogue_requirements)["profile"] == "Veka Softline 82"


def test_direct_chat_without_window_line_is_not_fabricated():
    from app.agent.runtime.navimind_position_ledger import (
        direct_chat_position_manifest,
    )
    assert direct_chat_position_manifest(
        "Utwórz mi dwie pozycje według PDF, który jest gdzieś na pulpicie"
    ) is None
    assert direct_chat_position_manifest("x" * 4001) is None


def test_v2_receives_only_active_window_when_user_typed_both_in_chat():
    from app.agent.runtime.navimind_position_ledger import (
        direct_chat_position_manifest,
    )
    from app.agent.runtime.navimind_work_mission import (
        WorkMission, scoped_v2_mission_goal,
    )
    chat = (
        "Przygotuj dwie pozycje w nowej niezapisanej ofercie.\n"
        "Pos. 1: 1 Stk Fenster 1500x1400\n"
        "Profil: Veka Perfectline\n"
        "Pos. 2: 1 Stk Fenster 1300x1200\n"
        "Profil: Veka Softline 82"
    )
    manifest = direct_chat_position_manifest(chat)
    assert manifest is not None and manifest.safe_to_sequence
    mission = WorkMission(
        task_id="test-2-win", revision=1, message_id=1,
        goal=chat, document_key="DRAFT/NEW",
        stage=WorkStage.READY,
        position_ledger=PositionLedger(manifest),
    )
    first = scoped_v2_mission_goal(mission)
    assert "1500" in first and "Veka Perfectline" in first
    assert "1300" not in first and "Veka Softline 82" not in first
    from dataclasses import replace
    second = scoped_v2_mission_goal(
        replace(mission, position_ledger=PositionLedger(
            manifest, active_index=1
        ))
    )
    assert "1300" in second and "Veka Softline 82" in second
    assert "1500" not in second and "Veka Perfectline" not in second
