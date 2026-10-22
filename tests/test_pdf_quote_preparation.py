from __future__ import annotations

from app.agent.adapters.pdf_document_adapter import PdfDocumentAdapter
from app.agent.adapters.pdf_ingestion_service import PdfIngestionService
from app.agent.runtime.agent_runtime import AgentRuntime
from app.agent.session.agent_session_store import AgentSessionStore
from tests.test_pdf_document_adapter import write_text_pdf


class SpyControlLoop:
    def __init__(self):
        self.observe_calls = 0
        self.run_calls = 0

    def observe_scene(self):
        self.observe_calls += 1
        raise AssertionError("Quote preparation must not observe the GUI.")

    def run(self, plan, context):
        self.run_calls += 1
        raise AssertionError("Quote preparation must not execute a GUI plan.")


def make_runtime(root):
    control_loop = SpyControlLoop()
    runtime = AgentRuntime(
        orchestrator=object(),
        plan_executor=object(),
        session_store=AgentSessionStore(),
        control_loop=control_loop,
        pdf_ingestion_service=PdfIngestionService(
            adapter=PdfDocumentAdapter(allowed_roots=(root,)),
        ),
    )
    return runtime, control_loop


def test_prepare_pdf_quote_returns_validated_context_without_gui_actions(tmp_path):
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
    runtime, control_loop = make_runtime(root)
    runtime.ingest_pdf(source, source_alias="offer-001")

    prepared = runtime.prepare_pdf_quote(
        "offer-001",
        request_message="Przygotuj ofertę na podstawie załączonego PDF.",
    )

    assert prepared.can_continue_to_offer_workflow is True
    assert prepared.requires_manual_review is False
    assert prepared.offer_context is not None
    assert prepared.offer_context.product_type == "window"
    assert prepared.offer_context.width == 1200
    assert prepared.offer_context.height == 1500
    assert prepared.offer_context.quantity == 2
    assert prepared.to_payload()["status"] == "validated"
    assert prepared.to_payload()["offer_context"]["width"] == 1200
    assert control_loop.observe_calls == 0
    assert control_loop.run_calls == 0


def test_prepare_pdf_quote_reports_missing_fields_without_creating_context(tmp_path):
    root = tmp_path / "approved"
    root.mkdir()
    source = root / "incomplete.pdf"
    write_text_pdf(source, ["Product: window", "Width: 1200 mm"])
    runtime, control_loop = make_runtime(root)
    runtime.ingest_pdf(source, source_alias="incomplete")

    prepared = runtime.prepare_pdf_quote(
        "incomplete",
        request_message="Przygotuj ofertę z tego PDF.",
    )

    assert prepared.can_continue_to_offer_workflow is False
    assert prepared.requires_manual_review is True
    assert prepared.offer_context is None
    assert prepared.validation.missing_fields == ("height",)
    payload = prepared.to_payload()
    assert payload["status"] == "manual_review"
    assert "height" in payload["validation"]["missing_fields"]
    assert control_loop.observe_calls == 0
    assert control_loop.run_calls == 0


def test_prepare_pdf_quote_blocks_source_with_any_ocr_needed_page(tmp_path):
    root = tmp_path / "approved"
    root.mkdir()
    source = root / "mixed.pdf"
    write_text_pdf(
        source,
        ["Product: window", "Width: 1200 mm", "Height: 1500 mm", ""],
    )
    runtime, control_loop = make_runtime(root)
    extraction = runtime.ingest_pdf(source, source_alias="mixed")
    assert extraction.needs_ocr is True

    prepared = runtime.prepare_pdf_quote(
        "mixed",
        request_message="Przygotuj ofertę na podstawie PDF.",
    )

    assert prepared.can_continue_to_offer_workflow is False
    assert prepared.offer_context is None
    assert prepared.extraction.ocr_required_pages == (4,)
    assert any(
        conflict.code == "unverified_source_provenance"
        for conflict in prepared.validation.conflicts
    )
    assert control_loop.observe_calls == 0
    assert control_loop.run_calls == 0


def test_prepare_pdf_quote_preserves_conflicting_dimensions_for_manual_review(tmp_path):
    root = tmp_path / "approved"
    root.mkdir()
    source = root / "conflicting.pdf"
    write_text_pdf(
        source,
        [
            "Product: window",
            "Width: 1200 mm",
            "Width: 1300 mm",
            "Height: 1500 mm",
        ],
    )
    runtime, control_loop = make_runtime(root)
    runtime.ingest_pdf(source, source_alias="conflicting")

    prepared = runtime.prepare_pdf_quote(
        "conflicting",
        request_message="Przygotuj ofertę z tego PDF.",
    )

    assert prepared.can_continue_to_offer_workflow is False
    assert prepared.offer_context is None
    assert any(
        conflict.code == "conflicting_width"
        for conflict in prepared.validation.conflicts
    )
    assert control_loop.observe_calls == 0
    assert control_loop.run_calls == 0


def test_prepare_pdf_quote_requires_an_ingested_trusted_source():
    runtime, control_loop = make_runtime(".")
    try:
        runtime.prepare_pdf_quote(
            "missing",
            request_message="Przygotuj ofertę.",
        )
    except ValueError as exc:
        assert "trusted, ingested PDF" in str(exc)
    else:
        raise AssertionError("Unregistered PDF sources must be rejected.")
    assert control_loop.observe_calls == 0
    assert control_loop.run_calls == 0
