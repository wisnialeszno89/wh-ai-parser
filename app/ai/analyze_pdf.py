"""Explicit legacy vision-based PDF-to-Excel command.

The previous module executed a remote model call and wrote fixed filenames at
import time. Importing this module is now side-effect free; model access and
file writes happen only when the CLI is invoked explicitly.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
from typing import Sequence

from app.utils.json_extractor import extract_json
from app.ai.prompt import VISION_SYSTEM_PROMPT
from app.vision.utils.encode_image import encode_image
from app.normalizer.normalize import normalize_window
from app.validator.validate import validate_construction
from app.utils.report import generate_report


def _client():
    """Build the OpenAI client lazily after the user explicitly invokes the CLI."""
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is required for legacy vision-based PDF analysis.")
    from openai import OpenAI

    return OpenAI(api_key=api_key)


def analyze_pdf(pdf_path: str | Path, *, model: str | None = None) -> list[dict[str, object]]:
    """Analyze each PDF page via the legacy vision path and return normalized records.

    This is a compatibility path for image-heavy construction drawings. It is
    not the structured quote-fact ingestion pipeline and does not authorize
    WindowHub execution. The caller must choose and validate an output path.
    """
    source = Path(pdf_path).expanduser().resolve(strict=True)
    if not source.is_file() or source.suffix.casefold() != ".pdf":
        raise ValueError("An existing .pdf file is required.")

    try:
        import fitz
    except ImportError as exc:
        raise RuntimeError("PDF rendering requires PyMuPDF (fitz).") from exc

    records: list[dict[str, object]] = []
    selected_model = (model or os.getenv("MODEL", "gpt-4.1-mini")).strip()
    if not selected_model:
        raise ValueError("Model name must not be empty.")

    # Do not allocate the remote client or render pages until the path has
    # been validated and the user has explicitly invoked this function.
    client = _client()
    with fitz.open(source) as document:
        if len(document) == 0:
            raise ValueError("The PDF contains no pages.")
        for index, page in enumerate(document):
            image_bytes = page.get_pixmap().tobytes("png")
            import base64
            encoded = base64.b64encode(image_bytes).decode("ascii")
            response = client.responses.create(
                model=selected_model,
                input=[
                    {"role": "system", "content": VISION_SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "input_text",
                                "text": (
                                    f"Analyze page {index + 1} of the supplied "
                                    "construction drawing. Return only valid JSON."
                                ),
                            },
                            {
                                "type": "input_image",
                                "image_url": f"data:image/png;base64,{encoded}",
                            },
                        ],
                    },
                ],
            )
            parsed = extract_json(response.output_text)
            if isinstance(parsed, dict):
                page_records = [parsed]
            elif isinstance(parsed, list):
                page_records = parsed
            else:
                raise ValueError(
                    f"Page {index + 1} returned an unsupported JSON shape."
                )
            for record in page_records:
                if not isinstance(record, dict):
                    raise ValueError(
                        f"Page {index + 1} returned a non-object construction record."
                    )
                normalized = normalize_window(record)
                errors = validate_construction(normalized)
                if errors:
                    raise ValueError(
                        f"Page {index + 1} failed construction validation: "
                        + "; ".join(str(error) for error in errors)
                    )
                records.append(normalized)
    return records


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Explicit legacy vision-based PDF analyzer. "
            "Importing this module does not access files or call a model."
        )
    )
    parser.add_argument("pdf", type=Path, help="Source PDF path.")
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Explicit output .xlsx path; source PDF is never overwritten.",
    )
    parser.add_argument("--model", default=None, help="Optional model override.")
    args = parser.parse_args(argv)

    source = args.pdf.expanduser().resolve()
    output = args.output.expanduser().resolve()
    if output.suffix.casefold() != ".xlsx":
        parser.error("--output must end in .xlsx")
    if output == source:
        parser.error("Output path must not overwrite the source PDF.")
    if output.exists():
        parser.error("Output file already exists; choose a new output path.")
    if not source.is_file() or source.suffix.casefold() != ".pdf":
        parser.error("Source must be an existing .pdf file.")
    output.parent.mkdir(parents=True, exist_ok=True)

    try:
        records = analyze_pdf(source, model=args.model)
        # Excel writes only after every page has been parsed and validated.
        import pandas as pd

        frame = pd.DataFrame(records)
        frame.to_excel(output, index=False)
        generate_report(records)
    except Exception as exc:
        # Avoid printing source contents, API credentials, or absolute paths.
        print(f"PDF analysis failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1

    print(f"Analyzed records: {len(records)}")
    print(f"Output workbook: {output.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
