"""Bounded, evidence-based conversational amendments for WindowHub offers.

Only deterministic, narrowly supported Polish phrases become structured
candidates. An LLM response by itself NEVER becomes an action, nor is a chat
message a native UI capability. Every candidate is bound to a single
human message, offer, mission revision and independently observed position.

The resulting change is staged and must be approved through MissionChat.
Execution remains disabled until a future verified native V2 integration.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import re

from app.agent.offers.navimind_quote_revision_planner import (
    QuoteChange, QuoteRevisionPlan, RevisionRoute, plan_quote_revision,
)
from app.agent.runtime.navimind_mission_chat import (
    ChangeState, ChatMessage, MessageRole, MissionChat,
)


class Field(str, Enum):
    COLOUR = "colour"
    WIDTH_MM = "width_mm"
    HEIGHT_MM = "height_mm"
    QUANTITY = "quantity"
    DESCRIPTION = "description"
    UNIT_PRICE = "unit_price"


class ProposalState(str, Enum):
    NEEDS_REVIEW = "needs_review"
    READY_FOR_REVIEW = "ready_for_review"


@dataclass(frozen=True)
class PositionEvidence:
    document_key: str
    position_id: str
    fields: dict[str, str]
    exact_document_verified: bool
    exact_position_verified: bool
    fresh: bool
    editable_fields: tuple[str, ...]


@dataclass(frozen=True)
class StructuredAmendment:
    position_id: str
    field: Field
    value: str


@dataclass(frozen=True)
class AmendmentProposal:
    state: ProposalState
    reason: str
    document_key: str
    mission_revision: int
    originating_message_id: int
    amendment: StructuredAmendment | None
    quote_plan: QuoteRevisionPlan | None
    request_id: int | None = None
    native_action_executed: bool = False
    customer_quote_saved: bool = False


_POSITION = re.compile(r"\b(?:poz(?:ycji|ycja|\.)?|poz)\s*\.?\s*(\d{1,3})\b", re.I)
_COLOUR = re.compile(
    r"\b(?:zmień|zmien|ustaw)\s+(?:kolor|barwę|barwe)\b.{0,80}"
    r"\b(?:na|jako)\s+(antracyt|biały|bialy|czarny|szary|brązowy|brazowy)\b",
    re.I,
)
_WIDTH = re.compile(
    r"\b(?:zmień|zmien|ustaw)\s+szerokość\b.{0,80}"
    r"\b(?:na|jako)\s*(\d{2,5})\s*(mm)?\b", re.I,
)
_HEIGHT = re.compile(
    r"\b(?:zmień|zmien|ustaw)\s+wysokość\b.{0,80}"
    r"\b(?:na|jako)\s*(\d{2,5})\s*(mm)?\b", re.I,
)
_QUANTITY = re.compile(
    r"\b(?:zmień|zmien|ustaw)\s+ilość\b.{0,80}"
    r"\b(?:na|jako)\s*(\d{1,3})\s*(?:szt\.?|sztuk)?\b", re.I,
)
_NEGATION = re.compile(r"\b(?:nie|bez)\s+(?:zmieniaj|zmien|ustawiaj|ustaw)\b", re.I)
_CURRENCY = re.compile(r"\b(?:pln|zł|eur|€)\b", re.I)


def parse_bounded_instruction(message: str) -> tuple[StructuredAmendment | None, str]:
    """Conservative single-field parser; unknown or ambiguous => review."""
    if not isinstance(message, str) or not message.strip() or len(message) > 1000:
        return None, "unbounded_or_empty_instruction"
    if _NEGATION.search(message):
        return None, "negated_instruction_requires_interpretation"
    # Extra commands must never silently piggyback on a recognized edit.
    if re.search(r"\b(?:zapisz|wyślij|wyslij|usuń|usun|zatwierdź|zatwierdz|"
                 r"zmień klienta|zmien klienta|dodaj pozycję|dodaj pozycje)\b",
                 message, re.I):
        return None, "mixed_or_persistent_instruction_requires_review"
    position_matches = list(_POSITION.finditer(message))
    if len(position_matches) != 1:
        return None, "exact_single_position_required"
    # Parse the WHOLE suffix after the position, not just a matching prefix.
    # Otherwise "pozycji 3 i 4 na antracyt" gets silently reduced to
    # position 3, and "pozycji 3 na antracyt i 4" is ignored as well.
    # This stage deliberately supports only one change to one position.
    suffix = message[position_matches[0].end():]
    supported_suffix = (
        r"\\s+(?:na|jako)\\s+"
        r"(?:antracyt|biały|bialy|czarny|szary|brązowy|brazowy|"
        r"\\d{1,5}(?:\\s*mm|\\s*szt\\.?|\\s*sztuk)?)\\s*"
    )
    if not re.fullmatch(supported_suffix, suffix, re.I):
        return None, "ambiguous_multiple_positions_or_trailing_instruction"
    found: list[tuple[Field, str]] = []
    for pattern, field in (
        (_COLOUR, Field.COLOUR),
        (_WIDTH, Field.WIDTH_MM),
        (_HEIGHT, Field.HEIGHT_MM),
        (_QUANTITY, Field.QUANTITY),
    ):
        matches = pattern.findall(message)
        if matches:
            if len(matches) != 1:
                return None, "ambiguous_repeated_field_instruction"
            captured = matches[0]
            value = captured if isinstance(captured, str) else captured[0]
            found.append((field, value.lower()))
    if len(found) != 1:
        return None, "single_supported_field_change_required"
    field, value = found[0]
    if field in (Field.WIDTH_MM, Field.HEIGHT_MM):
        mm = int(value)
        if not 100 <= mm <= 10000:
            return None, "dimension_outside_supported_range"
    if field == Field.QUANTITY and not 1 <= int(value) <= 99:
        return None, "quantity_outside_supported_range"
    return StructuredAmendment(position_matches[0].group(1), field, value), "recognized"


def prepare_amendment(
    chat: MissionChat, *,
    message_id: int,
    evidence: PositionEvidence,
    rebuild_possible: bool = True,
    rebuild_base_steps: int = 12,
) -> AmendmentProposal:
    """Translate one current human message to a pending review request.

    Checks exact readback, expected values, field editability, and minimum
    edit/rebuild costs before creating any approval request.
    """
    snapshot = chat.snapshot()
    matching = [
        m for m in snapshot.messages
        if m.message_id == message_id and m.role == MessageRole.HUMAN
        and m.mission_revision == snapshot.mission_revision
    ]
    if len(matching) != 1:
        raise ValueError("current_human_instruction_required")
    revision = snapshot.mission_revision
    change, reason = parse_bounded_instruction(matching[0].text)

    def rejected(message):
        return AmendmentProposal(
            ProposalState.NEEDS_REVIEW, message, chat.document_key,
            revision, message_id, change, None,
        )

    if change is None:
        return rejected(reason)
    if not (evidence.document_key == chat.document_key
            and evidence.position_id == change.position_id
            and evidence.exact_document_verified
            and evidence.exact_position_verified
            and evidence.fresh):
        return rejected("fresh_exact_position_evidence_required")
    current = evidence.fields.get(change.field.value)
    if current is None:
        return rejected("existing_field_value_not_verified")
    if current == change.value:
        return rejected("no_effective_change")
    if change.field.value not in evidence.editable_fields:
        return rejected("field_edit_not_proven_supported")
    # Affected fields may be compared only with observed values.
    quote_change = QuoteChange(
        position_id=change.position_id,
        field="dimensions" if change.field in (Field.WIDTH_MM, Field.HEIGHT_MM)
        else change.field.value,
        before=current, after=change.value,
        edit_steps=3, rebuild_steps=4,
        can_edit_existing=True, independently_observed=True,
    )
    plan = plan_quote_revision(
        document_key=chat.document_key,
        changes=(quote_change,),
        exact_document_verified=True,
        readback_fresh=True, rebuild_possible=rebuild_possible,
        rebuild_base_steps=rebuild_base_steps,
    )
    if plan.route == RevisionRoute.REVIEW:
        return rejected("quote_route_requires_review")
    # Proposal text is authored by local code, never copied from model
    # output. Review in MissionChat is still mandatory.
    request = chat.propose_change(
        originating_message_id=message_id,
        proposed_change=(
            f"Poz. {change.position_id}: {change.field.value} "
            f"{current!r} -> {change.value!r}; route={plan.route.value}"
        ),
        expected_revision=revision,
    )
    return AmendmentProposal(
        ProposalState.READY_FOR_REVIEW, "verified_change_waiting_for_approval",
        chat.document_key, revision, message_id, change, plan, request.request_id,
    )


def approved_amendment(chat: MissionChat, proposal: AmendmentProposal) -> StructuredAmendment:
    """Return pure data for a future V2 planner, NEVER execute GUI actions."""
    snapshot = chat.snapshot()
    if proposal.state != ProposalState.READY_FOR_REVIEW or proposal.amendment is None:
        raise ValueError("proposal_not_ready")
    if (proposal.document_key != chat.document_key
            or proposal.mission_revision != snapshot.mission_revision):
        raise ValueError("stale_or_wrong_document_proposal")
    matching = [
        c for c in snapshot.changes
        if c.request_id == proposal.request_id
        and c.document_key == chat.document_key
        and c.revision == proposal.mission_revision
        and c.originating_message_id == proposal.originating_message_id
        and c.state == ChangeState.APPROVED
    ]
    if len(matching) != 1:
        raise ValueError("explicit_salesperson_approval_required")
    plan = proposal.quote_plan
    if (plan is None or plan.target_document != chat.document_key
            or len(plan.changes) != 1
            or plan.changes[0].position_id != proposal.amendment.position_id
            or plan.changes[0].after != proposal.amendment.value):
        raise ValueError("proposal_binding_invalid")
    original = plan.changes[0].before
    expected_note = (
        f"Poz. {proposal.amendment.position_id}: {proposal.amendment.field.value} "
        f"{original!r} -> {proposal.amendment.value!r}; route={plan.route.value}"
    )
    if matching[0].proposed_change != expected_note:
        raise ValueError("proposal_binding_invalid")
    return proposal.amendment
