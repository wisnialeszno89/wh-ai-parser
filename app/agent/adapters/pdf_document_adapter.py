from __future__ import annotations

from dataclasses import dataclass
from importlib.util import find_spec
from pathlib import Path
from typing import Iterable

from app.agent.adapters.application_adapter import (
    AdapterDescriptor,
    ApplicationAdapter,
)


class PdfDocumentError(ValueError):
    """Structured, safe-to-serialize error from local PDF ingestion."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(message)

    def to_payload(self) -> dict[str, object]:
        return {
            "ok": False,
            "error": {
                "code": self.code,
                "message": self.message,
            },
        }


@dataclass(frozen=True)
class PdfPageFinding:
    """Text extracted from one PDF page with source provenance."""

    source_alias: str
    page_number: int
    text: str
    extraction_method: str
    extraction_confidence: float | None
    needs_ocr: bool
    limitations: tuple[str, ...] = ()

    def to_payload(self) -> dict[str, object]:
        return {
            "source_alias": self.source_alias,
            "page_number": self.page_number,
            "text": self.text,
            "extraction_method": self.extraction_method,
            "extraction_confidence": self.extraction_confidence,
            "needs_ocr": self.needs_ocr,
            "limitations": self.limitations,
        }


@dataclass(frozen=True)
class PdfDocumentExtraction:
    """Bounded local extraction result. No absolute source path is exposed."""

    source_alias: str
    page_count: int
    file_size_bytes: int
    status: str
    pages: tuple[PdfPageFinding, ...]

    @property
    def needs_ocr(self) -> bool:
        return any(page.needs_ocr for page in self.pages)

    @property
    def extracted_text_chars(self) -> int:
        return sum(len(page.text) for page in self.pages)

    def to_payload(self) -> dict[str, object]:
        return {
            "ok": True,
            "source_alias": self.source_alias,
            "page_count": self.page_count,
            "file_size_bytes": self.file_size_bytes,
            "status": self.status,
            "needs_ocr": self.needs_ocr,
            "extracted_text_chars": self.extracted_text_chars,
            "pages": tuple(page.to_payload() for page in self.pages),
        }


class PdfDocumentAdapter(ApplicationAdapter):
    """Read PDF text locally from explicitly approved filesystem roots.

    The adapter never calls a model, performs network I/O, writes output files,
    or modifies the source PDF. Textless pages are reported as needing OCR;
    this adapter does not silently treat them as successfully read content.
    """

    adapter_id = "pdf_document"
    EXTRACTION_METHOD = "pypdf_text"

    def __init__(
        self,
        *,
        allowed_roots: Iterable[str | Path],
        max_file_size_bytes: int = 25 * 1024 * 1024,
        max_pages: int = 100,
        max_page_chars: int = 40_000,
        max_total_chars: int = 200_000,
    ) -> None:
        roots = tuple(
            Path(root).expanduser().resolve()
            for root in allowed_roots
        )
        if not roots:
            raise ValueError("At least one allowed PDF root is required.")

        limits = {
            "max_file_size_bytes": max_file_size_bytes,
            "max_pages": max_pages,
            "max_page_chars": max_page_chars,
            "max_total_chars": max_total_chars,
        }
        invalid = [
            name
            for name, value in limits.items()
            if not isinstance(value, int) or isinstance(value, bool) or value < 1
        ]
        if invalid:
            raise ValueError(
                "PDF ingestion limits must be positive integers: "
                + ", ".join(invalid)
            )

        self._roots = roots
        self.max_file_size_bytes = max_file_size_bytes
        self.max_pages = max_pages
        self.max_page_chars = max_page_chars
        self.max_total_chars = max_total_chars

    @property
    def descriptor(self) -> AdapterDescriptor:
        return AdapterDescriptor(
            adapter_id=self.adapter_id,
            application="PDF",
            capabilities=("extract", "extract_text", "read_pdf"),
            description=(
                "Bounded, local PDF text extraction with page-level source "
                "provenance and explicit OCR-needed findings."
            ),
        )

    def is_available(self) -> bool:
        if not all(root.exists() and root.is_dir() for root in self._roots):
            return False
        try:
            return find_spec("pypdf") is not None
        except (ImportError, ValueError):
            return False

    @property
    def allowed_roots(self) -> tuple[Path, ...]:
        return self._roots

    def extract(
        self,
        path: str | Path,
        *,
        source_alias: str | None = None,
    ) -> PdfDocumentExtraction:
        source_path = self._resolve_source(path)
        alias = self._normalize_alias(source_alias, source_path.name)
        file_size = source_path.stat().st_size

        if file_size > self.max_file_size_bytes:
            raise PdfDocumentError(
                "file_size_limit_exceeded",
                "The PDF exceeds the configured file-size limit.",
            )

        try:
            from pypdf import PdfReader
        except ImportError as exc:
            raise PdfDocumentError(
                "pdf_dependency_missing",
                "PDF text extraction requires the pypdf package.",
            ) from exc

        try:
            with source_path.open("rb") as stream:
                reader = PdfReader(stream, strict=False)

                if reader.is_encrypted:
                    raise PdfDocumentError(
                        "encrypted_pdf",
                        "Encrypted PDFs are not supported without an approved password flow.",
                    )

                page_count = len(reader.pages)
                if page_count == 0:
                    raise PdfDocumentError(
                        "empty_pdf",
                        "The PDF contains no pages.",
                    )
                if page_count > self.max_pages:
                    raise PdfDocumentError(
                        "page_count_limit_exceeded",
                        "The PDF exceeds the configured page-count limit.",
                    )

                findings: list[PdfPageFinding] = []
                total_chars = 0

                for index, page in enumerate(reader.pages):
                    extraction_failed = False
                    try:
                        value = page.extract_text()
                        page_text = value if isinstance(value, str) else ""
                    except Exception:
                        # A page-local extraction failure is explicit and can
                        # be recovered by a later OCR/alternate-parser stage.
                        page_text = ""
                        extraction_failed = True

                    page_text = page_text.replace("\x00", "").strip()
                    if len(page_text) > self.max_page_chars:
                        raise PdfDocumentError(
                            "page_text_limit_exceeded",
                            "A PDF page exceeds the configured text-length limit.",
                        )

                    total_chars += len(page_text)
                    if total_chars > self.max_total_chars:
                        raise PdfDocumentError(
                            "document_text_limit_exceeded",
                            "The PDF exceeds the configured total extracted-text limit.",
                        )

                    needs_ocr = not page_text
                    limitations: tuple[str, ...] = ()
                    if extraction_failed:
                        limitations = (
                            "Text extraction failed for this page; OCR or an alternate parser is required.",
                        )
                    elif needs_ocr:
                        limitations = (
                            "No text was extracted; the page may be blank or image-only. OCR is required to inspect image content.",
                        )

                    findings.append(
                        PdfPageFinding(
                            source_alias=alias,
                            page_number=index + 1,
                            text=page_text,
                            extraction_method=self.EXTRACTION_METHOD,
                            # pypdf does not expose a calibrated confidence
                            # score, so do not invent one for extracted text.
                            extraction_confidence=None,
                            needs_ocr=needs_ocr,
                            limitations=limitations,
                        )
                    )

        except PdfDocumentError:
            raise
        except Exception as exc:
            raise PdfDocumentError(
                "invalid_pdf",
                "The PDF is malformed or could not be read safely.",
            ) from exc

        status = "ocr_required" if any(page.needs_ocr for page in findings) else "complete"
        return PdfDocumentExtraction(
            source_alias=alias,
            page_count=page_count,
            file_size_bytes=file_size,
            status=status,
            pages=tuple(findings),
        )

    def _resolve_source(self, path: str | Path) -> Path:
        if not isinstance(path, (str, Path)) or not str(path).strip():
            raise PdfDocumentError(
                "invalid_path",
                "An explicit PDF source path is required.",
            )

        try:
            resolved = Path(path).expanduser().resolve(strict=False)
        except (OSError, RuntimeError, ValueError) as exc:
            raise PdfDocumentError(
                "invalid_path",
                "The PDF source path is invalid.",
            ) from exc

        if not any(self._is_under_root(resolved, root) for root in self._roots):
            raise PdfDocumentError(
                "path_outside_allowed_roots",
                "The PDF path is outside all approved source roots.",
            )

        if resolved.suffix.casefold() != ".pdf":
            raise PdfDocumentError(
                "unsupported_file_type",
                "Only .pdf source files are supported.",
            )

        if not resolved.exists():
            raise PdfDocumentError(
                "file_not_found",
                "The PDF source file does not exist.",
            )

        if not resolved.is_file():
            raise PdfDocumentError(
                "not_a_file",
                "The PDF source path must refer to a file.",
            )

        return resolved

    @staticmethod
    def _is_under_root(path: Path, root: Path) -> bool:
        try:
            path.relative_to(root)
            return True
        except ValueError:
            return False

    @staticmethod
    def _normalize_alias(alias: str | None, default_name: str) -> str:
        value = default_name if alias is None else alias.strip() if isinstance(alias, str) else ""
        if (
            not value
            or len(value) > 160
            or "/" in value
            or "\\" in value
            or any(ord(char) < 32 for char in value)
        ):
            raise PdfDocumentError(
                "invalid_source_alias",
                "The source alias must be a short filename-like label without path separators.",
            )
        return value
