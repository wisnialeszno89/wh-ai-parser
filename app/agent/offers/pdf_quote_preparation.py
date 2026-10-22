"""Prepare and validate a local PDF quote without touching the GUI."""
from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass

from app.agent.adapters.pdf_document_adapter import PdfDocumentExtraction
from app.agent.offers.offer_context import OfferContext
from app.agent.offers.pdf_quote_fact_extractor import (
    PdfQuoteFactExtractionResult,
    PdfQuoteFactExtractor,
)
from app.agent.offers.quote_facts import (
    QuoteFactValidationResult,
    QuoteFactValidator,
    QuoteRuleEvidence,
)


@dataclass(frozen=True)
class PdfQuotePreparationResult:
    """Evidence, deterministic validation, and a context only when safe to use."""

    source_alias: str
    extraction: PdfQuoteFactExtractionResult
    validation: QuoteFactValidationResult
    offer_context: OfferContext | None

    @property
    def can_continue_to_offer_workflow(self) -> bool:
        return self.validation.can_execute and self.offer_context is not None

    @property
    def requires_manual_review(self) -> bool:
        return not self.can_continue_to_offer_workflow

    def to_payload(self) -> dict[str, object]:
        """Serialize a reviewable result without raw request text or local paths."""
        validation_payload = self.validation.to_payload()
        # Extraction already carries the source facts and evidence excerpts.
        validation_payload.pop("facts", None)

        context_payload: dict[str, object] | None = None
        if self.offer_context is not None:
            context = self.offer_context
            context_payload = {
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
                "missing_fields": list(context.missing_fields),
                "conflicts": list(context.conflicts),
            }

        return {
            "source_alias": self.source_alias,
            "status": (
                "validated"
                if self.can_continue_to_offer_workflow
                else "manual_review"
            ),
            "can_continue_to_offer_workflow": self.can_continue_to_offer_workflow,
            "requires_manual_review": self.requires_manual_review,
            "extraction": self.extraction.to_payload(),
            "validation": validation_payload,
            "offer_context": context_payload,
        }


class PdfQuotePreparationService:
    """Build typed facts and validate them against a trusted, ingested PDF."""

    def __init__(
        self,
        *,
        extractor: PdfQuoteFactExtractor | None = None,
        validator: QuoteFactValidator | None = None,
    ) -> None:
        self.extractor = extractor if extractor is not None else PdfQuoteFactExtractor()
        self.validator = validator if validator is not None else QuoteFactValidator()

    def prepare(
        self,
        extraction: PdfDocumentExtraction,
        *,
        known_sources: Mapping[str, object],
        request_message: str,
        approved_rules: Mapping[str, QuoteRuleEvidence] | Iterable[QuoteRuleEvidence] = (),
    ) -> PdfQuotePreparationResult:
        if not isinstance(extraction, PdfDocumentExtraction):
            raise TypeError(
                "PdfQuotePreparationService requires a PdfDocumentExtraction."
            )
        if known_sources.get(extraction.source_alias) is not extraction:
            raise ValueError(
                "PDF quote preparation requires the exact trusted registered extraction."
            )
        if not isinstance(request_message, str) or not request_message.strip():
            raise ValueError("A non-empty quote request message is required.")

        extracted_facts = self.extractor.extract(extraction)
        validation = self.validator.validate_payload(
            extracted_facts.to_payload(),
            request_message=request_message,
            pdf_sources=known_sources,
            approved_rules=approved_rules,
        )
        offer_context = (
            validation.to_offer_context(request_message)
            if validation.can_execute
            else None
        )
        return PdfQuotePreparationResult(
            source_alias=extraction.source_alias,
            extraction=extracted_facts,
            validation=validation,
            offer_context=offer_context,
        )
