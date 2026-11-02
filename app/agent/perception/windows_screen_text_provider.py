"""Application-neutral OCR perception for the active Windows desktop window."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable, Mapping
import math
import os

from app.agent.environment.environment_observation import EnvironmentObservation
from app.agent.perception.interaction_capability import InteractionCapability
from app.agent.perception.perception_provider import PerceptionProvider
from app.agent.perception.screen_element import ScreenElement
from app.agent.perception.semantic_evidence import (
    EvidenceKind,
    EvidenceSource,
    SemanticEvidence,
)


class WindowsScreenTextProvider(PerceptionProvider):
    """Extract bounded text lines from an already captured screenshot.

    OCR contributes text evidence only. It never marks OCR-only text as
    clickable, and therefore cannot independently authorize a mouse action.
    A separate accessibility provider must prove an actionable control.
    """

    MAX_WORDS = 3_000
    MAX_LINES = 200
    MAX_LINE_LENGTH = 500

    def __init__(
        self,
        *,
        ocr_runner: Callable[[object], Mapping[str, object]] | None = None,
        language: str | None = None,
        min_confidence: float = 35.0,
        max_lines: int = 100,
    ) -> None:
        if not math.isfinite(float(min_confidence)) or not 0 <= min_confidence <= 100:
            raise ValueError("windows_ocr_min_confidence_invalid")
        if isinstance(max_lines, bool) or not 1 <= max_lines <= self.MAX_LINES:
            raise ValueError("windows_ocr_max_lines_invalid")
        self._ocr_runner = ocr_runner
        self.language = (
            language.strip()
            if isinstance(language, str) and language.strip()
            else os.environ.get("COMPUTER_USE_OCR_LANG", "eng").strip() or "eng"
        )
        self.min_confidence = float(min_confidence)
        self.max_lines = max_lines

    def perceive(
        self,
        observation: EnvironmentObservation,
    ) -> tuple[ScreenElement, ...]:
        screenshot = observation.metadata.get("screenshot")
        image = getattr(screenshot, "image", None)
        if image is None:
            return ()

        try:
            data = (
                self._ocr_runner(image)
                if self._ocr_runner is not None
                else self._default_ocr(image)
            )
            return self._elements_from_data(
                data,
                width=getattr(screenshot, "width", None),
                height=getattr(screenshot, "height", None),
            )
        except Exception as exc:
            self._record_diagnostic(
                observation,
                status="unavailable",
                reason=type(exc).__name__,
            )
            return ()

    def _default_ocr(self, image) -> Mapping[str, object]:
        import cv2
        import numpy as np
        import pytesseract

        command = os.environ.get("TESSERACT_CMD", "").strip()
        if command:
            pytesseract.pytesseract.tesseract_cmd = command

        array = np.asarray(image)
        if array.ndim == 2:
            prepared = array
        elif array.ndim == 3 and array.shape[2] == 4:
            prepared = cv2.cvtColor(array, cv2.COLOR_BGRA2RGB)
        elif array.ndim == 3 and array.shape[2] == 3:
            prepared = cv2.cvtColor(array, cv2.COLOR_BGR2RGB)
        else:
            raise ValueError("windows_ocr_image_shape_unsupported")

        return pytesseract.image_to_data(
            prepared,
            lang=self.language,
            config="--psm 11",
            output_type=pytesseract.Output.DICT,
        )

    def _elements_from_data(
        self,
        data: Mapping[str, object],
        *,
        width: object,
        height: object,
    ) -> tuple[ScreenElement, ...]:
        if not isinstance(data, Mapping):
            raise TypeError("windows_ocr_result_invalid")

        text_values = data.get("text")
        if not isinstance(text_values, (list, tuple)):
            raise ValueError("windows_ocr_text_field_missing")

        count = min(len(text_values), self.MAX_WORDS)
        grouped: dict[tuple[int, int, int, int], list[tuple[int, str, float, int, int, int, int]]] = defaultdict(list)

        for index in range(count):
            raw_text = text_values[index]
            if not isinstance(raw_text, str):
                continue
            word = " ".join(raw_text.split())
            if not word:
                continue

            confidence = self._float_at(data, "conf", index, default=-1.0)
            if confidence < self.min_confidence:
                continue

            page = self._int_at(data, "page_num", index, default=1)
            block = self._int_at(data, "block_num", index, default=0)
            paragraph = self._int_at(data, "par_num", index, default=0)
            line = self._int_at(data, "line_num", index, default=index)
            word_order = self._int_at(data, "word_num", index, default=index)
            left = self._int_at(data, "left", index, default=-1)
            top = self._int_at(data, "top", index, default=-1)
            word_width = self._int_at(data, "width", index, default=0)
            word_height = self._int_at(data, "height", index, default=0)
            if left < 0 or top < 0 or word_width <= 0 or word_height <= 0:
                continue

            grouped[(page, block, paragraph, line)].append(
                (
                    word_order,
                    word,
                    confidence,
                    left,
                    top,
                    word_width,
                    word_height,
                )
            )

        elements: list[ScreenElement] = []
        for line_number, words in enumerate(grouped.values(), start=1):
            if len(elements) >= self.max_lines:
                break
            words.sort(key=lambda item: item[0])
            label = " ".join(item[1] for item in words).strip()
            if not label:
                continue
            label = label[: self.MAX_LINE_LENGTH]

            left = min(item[3] for item in words)
            top = min(item[4] for item in words)
            right = max(item[3] + item[5] for item in words)
            bottom = max(item[4] + item[6] for item in words)

            image_width = self._positive_dimension(width)
            image_height = self._positive_dimension(height)
            if image_width is not None:
                left = min(max(left, 0), image_width - 1)
                right = min(max(right, left + 1), image_width)
            if image_height is not None:
                top = min(max(top, 0), image_height - 1)
                bottom = min(max(bottom, top + 1), image_height)

            box_width = right - left
            box_height = bottom - top
            if box_width <= 0 or box_height <= 0:
                continue

            confidence = min(
                0.99,
                max(0.0, sum(item[2] for item in words) / len(words) / 100.0),
            )
            element_id = f"windows-ocr-line-{line_number}"
            label_evidence = SemanticEvidence(
                source=EvidenceSource.OCR,
                kind=EvidenceKind.LABEL,
                value=label,
                confidence=confidence,
                element_id=element_id,
            )
            text_evidence = SemanticEvidence(
                source=EvidenceSource.OCR,
                kind=EvidenceKind.TEXT,
                value=label,
                confidence=confidence,
                element_id=element_id,
            )
            bounds_evidence = SemanticEvidence(
                source=EvidenceSource.OCR,
                kind=EvidenceKind.BOUNDS,
                value=(left, top, box_width, box_height),
                confidence=confidence,
                element_id=element_id,
            )

            elements.append(
                ScreenElement(
                    kind="text",
                    label=label,
                    x=left,
                    y=top,
                    width=box_width,
                    height=box_height,
                    confidence=confidence,
                    interaction_capability=InteractionCapability.NOT_INTERACTIVE,
                    evidence=(
                        label_evidence,
                        text_evidence,
                        bounds_evidence,
                    ),
                    metadata={
                        "source": "windows_ocr",
                        "ocr_confidence": confidence,
                        "ocr_word_count": len(words),
                        "ocr_line_number": line_number,
                    },
                )
            )

        return tuple(elements)

    @staticmethod
    def _int_at(data: Mapping[str, object], key: str, index: int, *, default: int) -> int:
        values = data.get(key)
        if not isinstance(values, (list, tuple)) or index >= len(values):
            return default
        try:
            value = int(float(values[index]))
        except (TypeError, ValueError, OverflowError):
            return default
        return value

    @staticmethod
    def _float_at(data: Mapping[str, object], key: str, index: int, *, default: float) -> float:
        values = data.get(key)
        if not isinstance(values, (list, tuple)) or index >= len(values):
            return default
        try:
            value = float(values[index])
        except (TypeError, ValueError, OverflowError):
            return default
        return value if math.isfinite(value) else default

    @staticmethod
    def _positive_dimension(value: object) -> int | None:
        try:
            dimension = int(value)
        except (TypeError, ValueError, OverflowError):
            return None
        return dimension if dimension > 0 else None

    @staticmethod
    def _record_diagnostic(
        observation: EnvironmentObservation,
        *,
        status: str,
        reason: str,
    ) -> None:
        diagnostics = observation.metadata.setdefault(
            "perception_diagnostics",
            {},
        )
        if isinstance(diagnostics, dict):
            diagnostics["windows_ocr"] = {
                "status": status,
                "reason": reason,
            }
