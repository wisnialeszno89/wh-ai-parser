from __future__ import annotations

import math
from typing import Any

import cv2
import numpy as np

from app.agent.environment.environment_observation import EnvironmentObservation
from app.agent.perception.interaction_capability import InteractionCapability
from app.agent.perception.perception_provider import PerceptionProvider
from app.agent.perception.screen_element import ScreenElement
from app.agent.perception.semantic_evidence import EvidenceKind, EvidenceSource, SemanticEvidence
from app.agent.perception.windowhub_ocr_table_pipeline import reconstruct_windowhub_ocr_table_rows


class WindowHubOCRProvider(PerceptionProvider):
    """Expose OCR as non-interactive evidence and optionally reconstruct OFR tables."""

    PROVIDER_ID = "windowhub_ocr"

    def __init__(self, *, engine: Any | None = None, min_confidence: float = 0.35) -> None:
        if not 0.0 <= min_confidence <= 1.0:
            raise ValueError("min_confidence must be between 0.0 and 1.0")
        self._engine = engine
        self.min_confidence = min_confidence

    def _get_engine(self) -> Any:
        if self._engine is None:
            from rapidocr import RapidOCR
            self._engine = RapidOCR()
        return self._engine

    @staticmethod
    def _is_windowhub_table_target(observation: EnvironmentObservation) -> bool:
        metadata = observation.metadata
        state = getattr(observation, "state", None)
        title = str(getattr(state, "active_window_title", "") or "")
        return (
            metadata.get("source") == "windowhub"
            and metadata.get("window_focused") is True
            and "OFR/" in title.upper()
        )

    def _reconstruct_table_if_applicable(
        self,
        observation: EnvironmentObservation,
        elements: list[ScreenElement],
        image: np.ndarray,
    ) -> None:
        if not self._is_windowhub_table_target(observation):
            return
        metadata = observation.metadata
        try:
            reconstruction = reconstruct_windowhub_ocr_table_rows(
                tuple(elements), image, self._get_engine()
            )
        except Exception as exc:
            # Table reconstruction is auxiliary; normal OCR should still succeed.
            metadata["windowhub_ocr_table_status"] = "error"
            metadata["windowhub_ocr_table_error"] = type(exc).__name__
            metadata["windowhub_ocr_table_row_count"] = 0
            metadata["windowhub_ocr_table_complete_row_count"] = 0
            return
        metadata["windowhub_ocr_table_reconstruction"] = reconstruction
        metadata["windowhub_ocr_table_status"] = "ok" if reconstruction.rows else "no_rows"
        metadata["windowhub_ocr_table_row_count"] = len(reconstruction.rows)
        metadata["windowhub_ocr_table_complete_row_count"] = sum(
            row.complete for row in reconstruction.rows
        )
        metadata["windowhub_ocr_table_field_refinement_count"] = len(
            reconstruction.field_refinements
        )
        metadata["windowhub_ocr_table_lp_refinement_count"] = len(
            reconstruction.lp_refinements
        )

    def perceive(self, observation: EnvironmentObservation) -> tuple[ScreenElement, ...]:
        screenshot = observation.metadata.get("screenshot")
        image = getattr(screenshot, "image", screenshot)
        if image is None:
            observation.metadata["windowhub_ocr_status"] = "skipped_no_screenshot"
            observation.metadata["windowhub_ocr_element_count"] = 0
            return ()
        try:
            image = np.asarray(image)
            if image.size == 0 or image.ndim not in (2, 3):
                raise ValueError("Screenshot image is empty or has an invalid shape")
            if image.ndim == 2:
                image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
            elif image.shape[2] == 4:
                image = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)
            elif image.shape[2] != 3:
                raise ValueError("Screenshot must have 1, 3 or 4 channels")
            result = self._get_engine()(image)
        except Exception as exc:
            observation.metadata["windowhub_ocr_status"] = "error"
            observation.metadata["windowhub_ocr_error"] = type(exc).__name__
            observation.metadata["windowhub_ocr_element_count"] = 0
            return ()

        texts = getattr(result, "txts", None)
        boxes = getattr(result, "boxes", None)
        scores = getattr(result, "scores", None)
        if texts is None or boxes is None:
            observation.metadata["windowhub_ocr_status"] = "no_text"
            observation.metadata["windowhub_ocr_element_count"] = 0
            return ()

        image_height, image_width = image.shape[:2]
        elements: list[ScreenElement] = []
        for index, raw_text in enumerate(texts):
            text = str(raw_text).strip() if raw_text is not None else ""
            if not text or index >= len(boxes):
                continue
            try:
                confidence = (
                    float(scores[index])
                    if scores is not None and index < len(scores)
                    else 0.0
                )
                points = np.asarray(boxes[index], dtype=float).reshape(-1, 2)
            except (TypeError, ValueError, IndexError):
                continue
            if not math.isfinite(confidence) or confidence < self.min_confidence:
                continue
            if not 0.0 <= confidence <= 1.0 or len(points) < 4 or not np.isfinite(points).all():
                continue
            x1 = max(0, min(image_width, math.floor(float(points[:, 0].min()))))
            y1 = max(0, min(image_height, math.floor(float(points[:, 1].min()))))
            x2 = max(0, min(image_width, math.ceil(float(points[:, 0].max()))))
            y2 = max(0, min(image_height, math.ceil(float(points[:, 1].max()))))
            if x2 <= x1 or y2 <= y1:
                continue
            element_id = f"{self.PROVIDER_ID}-{index:04d}"
            bounds = (x1, y1, x2 - x1, y2 - y1)
            evidence = (
                SemanticEvidence(
                    source=EvidenceSource.OCR, kind=EvidenceKind.TEXT, value=text,
                    confidence=confidence, element_id=element_id,
                    metadata={"provider": self.PROVIDER_ID},
                ),
                SemanticEvidence(
                    source=EvidenceSource.OCR, kind=EvidenceKind.LABEL, value=text,
                    confidence=confidence, element_id=element_id,
                    metadata={"provider": self.PROVIDER_ID},
                ),
                SemanticEvidence(
                    source=EvidenceSource.OCR, kind=EvidenceKind.BOUNDS, value=bounds,
                    confidence=confidence, element_id=element_id,
                    metadata={"provider": self.PROVIDER_ID},
                ),
            )
            elements.append(ScreenElement(
                kind="text", label=text, x=x1, y=y1, width=x2 - x1, height=y2 - y1,
                confidence=confidence,
                metadata={
                    "source": self.PROVIDER_ID,
                    "provider_id": self.PROVIDER_ID,
                    "ocr_text": text,
                    "ocr_confidence": confidence,
                    "ocr_bounds": bounds,
                    "interaction_capability": InteractionCapability.UNKNOWN.value,
                    "interactive": False,
                },
                interaction_capability=InteractionCapability.UNKNOWN,
                evidence=evidence,
            ))

        self._reconstruct_table_if_applicable(observation, elements, image)
        observation.metadata["windowhub_ocr_status"] = "ok" if elements else "no_text_or_filtered"
        observation.metadata["windowhub_ocr_element_count"] = len(elements)
        return tuple(elements)
