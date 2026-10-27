"""Conservative deterministic extraction of quote facts from local PDF text.

Only explicit, line-scoped labels are accepted. This module does not call a
model, infer unlabeled dimensions, extract prices, or inspect OCR-needed pages.
Every produced fact retains the exact source alias, page, extraction method,
and complete evidence line so QuoteFactValidator can verify its provenance.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from app.agent.adapters.pdf_document_adapter import PdfDocumentExtraction
from app.agent.offers.quote_facts import (
    QuoteFact,
    QuoteFactSource,
    QuoteFactValidator,
)


# This score means the deterministic field-label/value rule matched exactly.
# It is not a calibrated OCR confidence score; OCR-needed pages are never read.
_DETERMINISTIC_MATCH_CONFIDENCE = 1.0

_LABELLED_TEXT = re.compile(
    r"^\s*(?:rodzaj\s+produktu|typ\s+produktu|produkt|"
    r"product(?:\s+type)?|type)\s*[:=]\s*(?P<value>.+?)\s*[.;]?\s*$",
    re.IGNORECASE,
)
_LABELLED_WIDTH = re.compile(
    r"^\s*(?:szerokość|szerokosc|width)\s*[:=]\s*"
    r"(?P<value>[+-]?\d+(?:[.,]\d+)?\s*(?:mm|cm|m)?)\s*[.;]?\s*$",
    re.IGNORECASE,
)
_LABELLED_HEIGHT = re.compile(
    r"^\s*(?:wysokość|wysokosc|height)\s*[:=]\s*"
    r"(?P<value>[+-]?\d+(?:[.,]\d+)?\s*(?:mm|cm|m)?)\s*[.;]?\s*$",
    re.IGNORECASE,
)
_LABELLED_QUANTITY = re.compile(
    r"^\s*(?:ilość|ilosc|quantity|qty)\s*[:=]\s*"
    r"(?P<value>[+-]?\d+)"
    r"(?:\s*(?:szt\.?|sztuk|sztuki|piece|pieces|pc|pcs))?\s*[.;]?\s*$",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class PdfQuoteFactExtractionResult:
    """Candidate facts plus OCR gaps, serializable for the quote-facts gate."""

    source_alias: str
    facts: tuple[QuoteFact, ...]
    ocr_required_pages: tuple[int, ...]

    @property
    def needs_ocr(self) -> bool:
        return bool(self.ocr_required_pages)

    def to_payload(self) -> dict[str, object]:
        """Return the versioned quote-facts envelope with explicit OCR gaps."""
        payload = QuoteFactValidator.envelope(self.facts)
        payload["source_alias"] = self.source_alias
        payload["ocr_required_pages"] = list(self.ocr_required_pages)
        payload["needs_ocr"] = self.needs_ocr
        return payload


class PdfQuoteFactExtractor:
    """Extract only explicitly labelled, page-attributed facts from PDF text."""

    def extract(
        self,
        extraction: PdfDocumentExtraction,
    ) -> PdfQuoteFactExtractionResult:
        if not isinstance(extraction, PdfDocumentExtraction):
            raise TypeError(
                "PdfQuoteFactExtractor requires a PdfDocumentExtraction."
            )

        facts: list[QuoteFact] = []
        ocr_pages: list[int] = []

        for page in extraction.pages:
            if page.needs_ocr:
                ocr_pages.append(page.page_number)
                continue

            # PDF libraries may use different line boundaries. Each non-empty
            # line is checked independently; we never combine nearby text or
            # infer values from unlabeled prose.
            for raw_line in page.text.splitlines():
                evidence_text = raw_line.strip()
                if not evidence_text:
                    continue

                candidates = (
                    ("product_type", _LABELLED_TEXT),
                    ("width", _LABELLED_WIDTH),
                    ("height", _LABELLED_HEIGHT),
                    ("quantity", _LABELLED_QUANTITY),
                )
                for field_name, pattern in candidates:
                    match = pattern.fullmatch(evidence_text)
                    if match is None:
                        continue

                    raw_value = match.group("value").strip().rstrip(" .;\t")
                    if not raw_value:
                        continue

                    if page.extraction_method == "pypdf_text":
                        fact_confidence = _DETERMINISTIC_MATCH_CONFIDENCE
                    else:
                        normalized_evidence = " ".join(evidence_text.casefold().split())
                        matching_scores = [
                            region.confidence
                            for region in page.ocr_regions
                            if region.confidence is not None
                            and " ".join(region.text.casefold().split()) in normalized_evidence
                        ]
                        fact_confidence = (
                            min(matching_scores)
                            if matching_scores
                            else page.extraction_confidence or 0.0
                        )

                    facts.append(
                        QuoteFact(
                            field_name=field_name,
                            raw_value=raw_value,
                            source=QuoteFactSource(
                                source_alias=page.source_alias,
                                page_number=page.page_number,
                                extraction_method=page.extraction_method,
                                source_kind=(
                                    "image_document"
                                    if extraction.source_type == "image"
                                    else "pdf_document"
                                ),
                            ),
                            confidence=min(
                                _DETERMINISTIC_MATCH_CONFIDENCE,
                                max(0.0, min(1.0, fact_confidence)),
                            ),
                            origin="source_fact",
                            unit="piece" if field_name == "quantity" else None,
                            evidence_text=evidence_text,
                        )
                    )
                    break

        return PdfQuoteFactExtractionResult(
            source_alias=extraction.source_alias,
            facts=tuple(facts),
            ocr_required_pages=tuple(ocr_pages),
        )
