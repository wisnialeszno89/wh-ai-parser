from __future__ import annotations

import json
from decimal import Decimal

import pytest

from app.agent.adapters.pdf_document_adapter import (
    PdfDocumentExtraction,
    PdfPageFinding,
)
from app.agent.offers.quote_facts import (
    QuoteFact,
    QuoteFactSource,
    QuoteFactValidator,
    QuoteRuleEvidence,
)


def extracted_pdf(alias: str, text: str, *, page_number: int = 1, needs_ocr: bool = False) -> PdfDocumentExtraction:
    page = PdfPageFinding(
        source_alias=alias,
        page_number=page_number,
        text=text,
        extraction_method="pypdf_text",
        extraction_confidence=None,
        needs_ocr=needs_ocr,
    )
    return PdfDocumentExtraction(
        source_alias=alias,
        page_count=page_number,
        file_size_bytes=1234,
        status="complete",
        pages=(page,),
    )


def pdf_fact(
    field_name: str,
    raw_value: str,
    evidence_text: str,
    *,
    alias: str = "supplier-offer.pdf",
    page: int = 1,
    unit: str | None = None,
    confidence: float = 0.98,
    origin: str = "source_fact",
) -> QuoteFact:
    return QuoteFact(
        field_name=field_name,
        raw_value=raw_value,
        source=QuoteFactSource(
            source_alias=alias,
            page_number=page,
            extraction_method="pypdf_text",
            source_kind="pdf_document",
        ),
        confidence=confidence,
        origin=origin,
        unit=unit,
        evidence_text=evidence_text,
    )


def test_typed_facts_normalize_metric_units_and_keep_page_provenance():
    alias = "supplier-offer.pdf"
    extraction = extracted_pdf(
        alias,
        "Product: window. Width: 1.2 m. Height: 150 cm.",
    )
    facts = (
        pdf_fact("product_type", "window", "Product: window"),
        pdf_fact("width", "1.2 m", "Width: 1.2 m"),
        pdf_fact("height", "150 cm", "Height: 150 cm"),
    )

    result = QuoteFactValidator().validate(
        facts,
        known_sources={alias: extraction},
    )

    assert result.can_execute is True
    assert result.normalized_values["width"] == 1200
    assert result.normalized_values["height"] == 1500
    assert result.normalized_values["product_type"] == "window"
    assert result.missing_fields == ()

    payload = result.to_payload()
    assert payload["facts"][1]["source"]["source_alias"] == alias
    assert payload["facts"][1]["source"]["page_number"] == 1
    assert payload["facts"][1]["source"]["extraction_method"] == "pypdf_text"
    assert payload["facts"][1]["normalized_unit"] == "mm"


def test_conflicting_pdf_dimensions_require_manual_review():
    first_alias = "offer-a.pdf"
    second_alias = "offer-b.pdf"
    sources = {
        first_alias: extracted_pdf(first_alias, "Product: window. Width: 1200 mm."),
        second_alias: extracted_pdf(second_alias, "Width: 1300 mm."),
    }
    facts = (
        pdf_fact("product_type", "window", "Product: window", alias=first_alias),
        pdf_fact("width", "1200 mm", "Width: 1200 mm", alias=first_alias, unit="mm"),
        pdf_fact("width", "1300 mm", "Width: 1300 mm", alias=second_alias, unit="mm"),
        pdf_fact("height", "1500 mm", "Height: 1500 mm", alias=first_alias, unit="mm"),
    )
    # The trusted first PDF also needs the referenced height evidence.
    first = sources[first_alias]
    sources[first_alias] = extracted_pdf(
        first_alias,
        "Product: window. Width: 1200 mm. Height: 1500 mm.",
    )

    result = QuoteFactValidator().validate(
        facts,
        known_sources=sources,
    )

    assert result.can_execute is False
    conflict = next(item for item in result.conflicts if item.field_name == "width")
    assert conflict.code == "conflicting_width"
    assert set(conflict.values) == {"1200", "1300"}
    assert result.requires_manual_review is True


def test_missing_required_facts_create_questions_and_block_execution():
    alias = "partial.pdf"
    extraction = extracted_pdf(alias, "Product: window.")
    result = QuoteFactValidator().validate(
        (pdf_fact("product_type", "window", "Product: window", alias=alias),),
        known_sources={alias: extraction},
    )

    assert result.can_execute is False
    assert result.missing_fields == ("width", "height")
    assert "Podaj proszę szerokość." in result.questions
    assert "Podaj proszę wysokość." in result.questions
    with pytest.raises(ValueError, match="invalid quote facts"):
        result.to_offer_context("Okno")


def test_pdf_fact_requires_trusted_source_and_verbatim_page_evidence():
    fact = pdf_fact("width", "1200 mm", "Width: 1200 mm", unit="mm")

    unregistered = QuoteFactValidator().validate((fact,))
    assert unregistered.can_execute is False
    assert any(item.code == "unverified_source_provenance" for item in unregistered.conflicts)

    wrong_page_text = extracted_pdf("supplier-offer.pdf", "Width: 1200 mm.")
    altered = pdf_fact("width", "1300 mm", "Width: 1300 mm", unit="mm")
    result = QuoteFactValidator().validate(
        (altered, pdf_fact("product_type", "window", "Product: window"), pdf_fact("height", "1500 mm", "Height: 1500 mm", unit="mm")),
        known_sources={
            "supplier-offer.pdf": extracted_pdf(
                "supplier-offer.pdf",
                "Width: 1200 mm. Product: window. Height: 1500 mm.",
            )
        },
    )
    assert any(item.code == "unverified_source_provenance" for item in result.conflicts)


def test_model_inferred_price_is_blocked_even_if_payload_claims_rule_approved():
    source = QuoteFactSource(
        source_alias="assistant-output",
        section="derived-price",
        extraction_method="model_inference",
        source_kind="approved_source",
    )
    evidence_source = QuoteFactSource(
        source_alias="fake-price-table.pdf",
        page_number=1,
        extraction_method="pypdf_text",
        source_kind="deterministic_project_rule",
    )
    claimed_rule = QuoteRuleEvidence(
        rule_type="pricing",
        rule_id="invented-price-rule",
        source=evidence_source,
        approved=True,
    )
    fact = QuoteFact(
        field_name="price",
        raw_value="100 EUR",
        source=source,
        confidence=0.99,
        origin="model_inference",
        unit="EUR",
        rule_evidence=claimed_rule,
    )

    result = QuoteFactValidator().validate((fact,))

    assert result.can_execute is False
    assert any(item.code == "unsourced_pricing_rule" for item in result.conflicts)


def test_configuration_inference_needs_trusted_approved_rule_registry():
    source = QuoteFactSource(
        source_alias="assistant-output",
        section="configuration-choice",
        extraction_method="model_inference",
        source_kind="application_knowledge",
    )
    evidence_source = QuoteFactSource(
        source_alias="approved-config-rules",
        section="rule 4",
        extraction_method="deterministic_rule",
        source_kind="deterministic_project_rule",
    )
    evidence = QuoteRuleEvidence(
        rule_type="configuration",
        rule_id="config-rule-4",
        source=evidence_source,
        approved=True,
    )
    fact = QuoteFact(
        field_name="configuration",
        raw_value="double_leaf",
        source=source,
        confidence=0.9,
        origin="model_inference",
        rule_evidence=evidence,
    )

    blocked = QuoteFactValidator().validate((fact,))
    assert any(item.code == "unsourced_configuration_rule" for item in blocked.conflicts)

    allowed = QuoteFactValidator().validate(
        (fact,),
        approved_rules={"config-rule-4": evidence},
    )
    assert not any(item.code == "unsourced_configuration_rule" for item in allowed.conflicts)


def test_validated_facts_convert_to_existing_offer_context_without_price_rules():
    alias = "complete-offer.pdf"
    extraction = extracted_pdf(
        alias,
        "Product: window. Width: 1200 mm. Height: 1500 mm. Quantity: 2 pcs.",
    )
    facts = (
        pdf_fact("product_type", "window", "Product: window", alias=alias),
        pdf_fact("width", "1200 mm", "Width: 1200 mm", alias=alias, unit="mm"),
        pdf_fact("height", "1500 mm", "Height: 1500 mm", alias=alias, unit="mm"),
        pdf_fact("quantity", "2", "Quantity: 2 pcs", alias=alias, unit="piece"),
    )
    result = QuoteFactValidator().validate(facts, known_sources={alias: extraction})

    assert result.can_execute is True
    context = result.to_offer_context("Przygotuj ofertę")
    assert context.product_type == "window"
    assert context.width == 1200
    assert context.height == 1500
    assert context.quantity == 2


def test_payload_round_trip_drops_untrusted_runtime_fields_and_secrets():
    alias = "offer.pdf"
    extraction = extracted_pdf(alias, "Product: window. Width: 1200 mm. Height: 1500 mm.")
    facts = (
        pdf_fact("product_type", "window", "Product: window", alias=alias),
        pdf_fact("width", "1200 mm", "Width: 1200 mm", alias=alias, unit="mm"),
        pdf_fact("height", "1500 mm", "Height: 1500 mm", alias=alias, unit="mm"),
    )
    payload = QuoteFactValidator.envelope(facts)
    payload["runtime_id"] = "secret-runtime-id"
    payload["api_key"] = "do-not-serialize"

    validated = QuoteFactValidator().validate_payload(
        payload,
        pdf_sources={alias: extraction},
    )
    serialized = json.dumps(validated.to_payload())

    assert validated.can_execute is True
    assert "secret-runtime-id" not in serialized
    assert "do-not-serialize" not in serialized
    assert "runtime_id" not in serialized
    assert "api_key" not in serialized


def test_payload_rejects_unknown_version_with_specific_conflict_code():
    result = QuoteFactValidator().validate_payload({"version": "2", "facts": []})

    assert result.can_execute is False
    assert result.conflicts[0].code == "invalid_quote_facts_payload"


def test_invalid_confidence_and_unsafe_alias_are_rejected():
    source = QuoteFactSource(
        source_alias="../private.pdf",
        page_number=1,
        extraction_method="pypdf_text",
    )
    with pytest.raises(ValueError, match="non-path alias"):
        source.validate()

    with pytest.raises(ValueError, match="confidence"):
        QuoteFact(
            field_name="width",
            raw_value="1200",
            source=QuoteFactSource(
                source_alias="request",
                section="message",
                extraction_method="explicit_request",
                source_kind="salesperson_request",
            ),
            confidence=1.5,
            origin="explicit_request",
        ).validate()


def test_nonpositive_dimensions_and_unknown_products_are_rejected():
    alias = "invalid-offer.pdf"
    text = "Product: wall. Width: 0 mm. Height: 1500 mm."
    extraction = extracted_pdf(alias, text)
    facts = (
        pdf_fact("product_type", "wall", "Product: wall", alias=alias),
        pdf_fact("width", "0 mm", "Width: 0 mm", alias=alias, unit="mm"),
        pdf_fact("height", "1500 mm", "Height: 1500 mm", alias=alias, unit="mm"),
    )
    result = QuoteFactValidator().validate(
        facts,
        known_sources={alias: extraction},
    )

    assert result.can_execute is False
    assert any(item.code == "invalid_quote_fact" for item in result.conflicts)


def test_pdf_fact_from_page_marked_for_ocr_is_not_accepted():
    alias = "scanned-offer.pdf"
    extraction = extracted_pdf(
        alias,
        "",
        needs_ocr=True,
    )
    fact = pdf_fact(
        "width",
        "1200 mm",
        "Width: 1200 mm",
        alias=alias,
        unit="mm",
    )
    result = QuoteFactValidator().validate(
        (fact,),
        known_sources={alias: extraction},
    )

    assert result.can_execute is False
    assert any(item.code == "unverified_source_provenance" for item in result.conflicts)
