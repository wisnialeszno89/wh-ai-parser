"""Bridge a validated PDF quote preview into an approval-gated task checkpoint."""
from __future__ import annotations

from dataclasses import dataclass

from app.agent.offers.pdf_quote_preparation import PdfQuotePreparationResult
from app.agent.offers.quote_facts import QuoteFactValidator
from app.agent.runtime.resumable_task import TaskCheckpoint, TaskStatus


@dataclass(frozen=True)
class PdfQuoteTaskStartResult:
    """Preparation outcome plus a persisted checkpoint when safely eligible."""

    preparation: PdfQuotePreparationResult
    checkpoint: TaskCheckpoint | None
    task_block_reason: str | None = None

    @property
    def task_created(self) -> bool:
        return self.checkpoint is not None

    @property
    def requires_manual_review(self) -> bool:
        return (
            self.preparation.requires_manual_review
            or self.checkpoint is None
        )

    def to_payload(self) -> dict[str, object]:
        return {
            "status": (
                "waiting_for_approval"
                if self.checkpoint is not None
                else "manual_review"
            ),
            "task_created": self.task_created,
            "requires_manual_review": self.requires_manual_review,
            "task_block_reason": self.task_block_reason,
            "preparation": self.preparation.to_payload(),
            "checkpoint": self.checkpoint.to_payload() if self.checkpoint else None,
        }


class UnsupportedWindowHubQuoteFields(ValueError):
    """A quote contains values not yet supported by safe WindowHub verification."""


def create_pdf_quote_task_checkpoint(
    preparation: PdfQuotePreparationResult,
    *,
    task_id: str,
    max_actions: int = 12,
    max_reasoning_calls: int = 12,
) -> TaskCheckpoint:
    """Create a local checkpoint that cannot advance before explicit approval."""
    if not isinstance(preparation, PdfQuotePreparationResult):
        raise TypeError("preparation must be a PdfQuotePreparationResult.")
    if not preparation.can_continue_to_offer_workflow or preparation.offer_context is None:
        raise ValueError("A task checkpoint requires a fully validated PDF quote preparation.")

    context = preparation.offer_context
    candidate_facts = {
        "product_type": context.product_type,
        "width": context.width,
        "height": context.height,
        "quantity": context.quantity,
        "profile": context.profile,
        "configuration": context.configuration,
        "opening": context.opening,
        "openings": list(context.openings),
        "color_inside": context.color_inside,
        "color_outside": context.color_outside,
        "glazing": context.glazing,
    }
    validated_fields = tuple(preparation.validation.normalized_values)
    supported_fields = {"product_type", "width", "height", "quantity"}
    unsupported_fields = tuple(
        sorted(set(validated_fields).difference(supported_fields))
    )
    if unsupported_fields:
        raise UnsupportedWindowHubQuoteFields(
            "WindowHub draft automation does not yet safely verify these quote "
            "fields: " + ", ".join(unsupported_fields)
        )

    # Only fields backed by the deterministic validator enter the task prompt.
    # Domain defaults that were not evidenced by the PDF/request are not facts.
    facts = {
        key: candidate_facts[key]
        for key in validated_fields
        if key in candidate_facts and candidate_facts[key] is not None
    }

    citations = tuple(
        {
            "field_name": fact.field_name,
            "raw_value": fact.raw_value,
            "evidence_text": fact.evidence_text,
            "source": fact.source.to_payload(),
        }
        for fact in preparation.extraction.facts
    )
    return TaskCheckpoint(
        task_id=task_id,
        goal="Prepare a draft WindowHub offer from a validated local PDF.",
        facts=facts,
        required_fields=tuple(dict.fromkeys((
            *QuoteFactValidator.REQUIRED_FIELDS,
            *validated_fields,
        ))),
        unresolved_issues=(),
        citations=citations,
        expected_application="WindowHub",
        status=TaskStatus.WAITING_FOR_APPROVAL,
        max_actions=max_actions,
        max_reasoning_calls=max_reasoning_calls,
        draft_only=True,
        approval_required=True,
        execution_approved=False,
    )
