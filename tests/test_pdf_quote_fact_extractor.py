from __future__ import annotations

from dataclasses import replace

import pytest

from app.agent.adapters.pdf_document_adapter import (
    PdfDocumentAdapter,
    PdfDocumentExtraction,
)
from app.agent.adapters.pdf_ingestion_service import PdfIngestionService
from app.agent.offers.pdf_quote_fact_extractor import PdfQuoteFactExtractor
from app.agent.offers.quote_facts import QuoteFactValidator
from app.agent.runtime.agent_runtime import AgentRuntime
from app.agent.session.agent_session_store import AgentSessionStore
from tests.test_pdf_document_adapter import write_text_pdf


def make_runtime(root):
    service = PdfIngestionService(
        adapter=PdfDocumentAdapter(allowed_roots=(root,)),
    )
    return AgentRuntime(
        orchestrator=object(),
        plan_executor=object(),
        session_store=AgentSessionStore(),
        pdf_ingestion_service=service,
    )


def test_runtime_extracts_labelled_pdf_facts_with_exact_page_evidence(tmp_path):
    root = tmp_path / "approved"
    root.mkdir()
    source = root / "offer.pdf"
    write_text_pdf(
        source,
        [
            "Product: window",
            "Width: 1200 mm",
            "Height: 1500 mm",
            "Quantity: 2 pcs",
        ],
    )
    runtime = make_runtime(root)
    extracted = runtime.ingest_pdf(source, source_alias="offer-001")

    payload = runtime.extract_pdf_quote_facts("offer-001")

    assert payload["version"] == "1"
    assert payload["source_alias"] == "offer-001"
    assert payload["needs_ocr"] is False
    assert payload["ocr_required_pages"] == []
    assert {
        (fact["field_name"], fact["raw_value"], fact["source"]["page_number"])
        for fact in payload["facts"]
    } == {
        ("product_type", "window", 1),
        ("width", "1200 mm", 2),
        ("height", "1500 mm", 3),
        ("quantity", "2", 4),
    }
    assert all(
        fact["evidence_text"] in extracted.pages[fact["source"]["page_number"] - 1].text
        for fact in payload["facts"]
    )
    assert all(
        fact["source"]["source_alias"] == "offer-001"
        and fact["source"]["extraction_method"] == "pypdf_text"
        for fact in payload["facts"]
    )

    validation = QuoteFactValidator().validate_payload(
        payload,
        pdf_sources=runtime.registered_pdf_sources(),
    )
    assert validation.can_execute is True
    assert validation.normalized_values["product_type"] == "window"
    assert validation.normalized_values["width"] == 1200
    assert validation.normalized_values["height"] == 1500
    assert validation.normalized_values["quantity"] == 2


def test_runtime_refuses_to_extract_a_pdf_alias_that_was_not_ingested():
    runtime = AgentRuntime(
        orchestrator=object(),
        plan_executor=object(),
        session_store=AgentSessionStore(),
    )

    with pytest.raises(ValueError, match="trusted, ingested PDF"):
        runtime.extract_pdf_quote_facts("not-registered")


def test_extractor_skips_ocr_needed_page_and_reports_the_gap(tmp_path):
    root = tmp_path / "approved"
    root.mkdir()
    source = root / "mixed.pdf"
    write_text_pdf(source, ["Product: window", "Width: 1200 mm", "Height: 1500 mm"])
    extraction = PdfDocumentAdapter(allowed_roots=(root,)).extract(source, source_alias="mixed")
    changed_page = replace(extraction.pages[1], needs_ocr=True, limitations=("OCR pending",))
    mixed = replace(
        extraction,
        status="ocr_required",
        pages=(extraction.pages[0], changed_page, extraction.pages[2]),
    )

    result = PdfQuoteFactExtractor().extract(mixed)

    assert result.needs_ocr is True
    assert result.ocr_required_pages == (2,)
    assert [fact.field_name for fact in result.facts] == ["product_type", "height"]
    payload = result.to_payload()
    assert payload["needs_ocr"] is True
    assert payload["ocr_required_pages"] == [2]

    validation = QuoteFactValidator().validate_payload(
        payload,
        pdf_sources={"mixed": mixed},
    )
    assert validation.requires_manual_review is True
    assert any(
        conflict.code == "unverified_source_provenance"
        for conflict in validation.conflicts
    )


def test_unlabelled_prose_does_not_become_guessed_quote_facts(tmp_path):
    root = tmp_path / "approved"
    root.mkdir()
    source = root / "notes.pdf"
    write_text_pdf(
        source,
        ["Please consider a window measuring 1200 x 1500 for the project."],
    )
    extraction = PdfDocumentAdapter(allowed_roots=(root,)).extract(source, source_alias="notes")

    result = PdfQuoteFactExtractor().extract(extraction)
    validation = QuoteFactValidator().validate_payload(
        result.to_payload(),
        pdf_sources={"notes": extraction},
    )

    assert result.facts == ()
    assert validation.requires_manual_review is True
    assert set(validation.missing_fields) == {"product_type", "width", "height"}


def test_conflicting_explicit_dimensions_remain_separate_and_fail_validation(tmp_path):
    root = tmp_path / "approved"
    root.mkdir()
    source = root / "conflict.pdf"
    write_text_pdf(
        source,
        [
            "Product: window",
            "Width: 1200 mm",
            "Width: 1300 mm",
            "Height: 1500 mm",
        ],
    )
    extraction = PdfDocumentAdapter(allowed_roots=(root,)).extract(source, source_alias="conflict")
    result = PdfQuoteFactExtractor().extract(extraction)

    validation = QuoteFactValidator().validate_payload(
        result.to_payload(),
        pdf_sources={"conflict": extraction},
    )

    assert [fact.raw_value for fact in result.facts if fact.field_name == "width"] == [
        "1200 mm",
        "1300 mm",
    ]
    assert validation.requires_manual_review is True
    assert any(conflict.code == "conflicting_width" for conflict in validation.conflicts)


def test_extractor_requires_a_pdf_document_extraction():
    with pytest.raises(TypeError, match="PdfDocumentExtraction"):
        PdfQuoteFactExtractor().extract(object())  # type: ignore[arg-type]
