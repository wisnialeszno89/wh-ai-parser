"""Trusted local PDF ingestion for provenance-aware agent workflows.

This service is the only place in this layer that turns a caller-approved local
PDF path into a trusted extraction registry entry. It never calls a model,
performs network I/O, or writes output files.
"""
from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from app.agent.adapters.pdf_document_adapter import (
    PdfDocumentAdapter,
    PdfDocumentError,
    PdfDocumentExtraction,
)


class PdfIngestionService:
    """Extract local PDFs and retain in-process source objects for fact validation."""

    def __init__(
        self,
        *,
        adapter: PdfDocumentAdapter,
        source_registry: dict[str, PdfDocumentExtraction] | None = None,
    ) -> None:
        if not isinstance(adapter, PdfDocumentAdapter):
            raise TypeError("PdfIngestionService requires a PdfDocumentAdapter.")
        self.adapter = adapter
        self._source_registry = source_registry if source_registry is not None else {}

    @property
    def source_registry(self) -> Mapping[str, PdfDocumentExtraction]:
        """Return a read-only view of trusted extractions owned by this service."""
        from types import MappingProxyType

        return MappingProxyType(self._source_registry)

    def ingest(
        self,
        path: str | Path,
        *,
        source_alias: str | None = None,
    ) -> PdfDocumentExtraction:
        """Read a file through the adapter and register only the returned object."""
        extraction = self.adapter.extract(path, source_alias=source_alias)
        if extraction.status not in {"complete", "ocr_required", "ocr_applied"}:
            raise PdfDocumentError(
                "invalid_extraction_status",
                "The PDF extraction did not return a supported status.",
            )
        existing = self._source_registry.get(extraction.source_alias)
        if existing is not None and existing != extraction:
            raise PdfDocumentError(
                "source_alias_collision",
                "A different extraction already uses this source alias.",
            )
        self._source_registry[extraction.source_alias] = extraction
        return extraction

    def remove(self, source_alias: str) -> bool:
        """Remove one source from the in-process trust registry."""
        return self._source_registry.pop(source_alias, None) is not None
