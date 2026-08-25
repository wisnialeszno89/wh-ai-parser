from __future__ import annotations

import base64
import hashlib
import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import cv2
import numpy as np


@dataclass(frozen=True)
class AIVisualElement:
    id: str
    kind: str
    side: str | None
    parent_id: str | None
    bbox: tuple[int, int, int, int] | None
    confidence: float
    properties: dict[str, Any]


@dataclass(frozen=True)
class AIVisualObservation:
    status: str
    confidence: float
    analysis_rect: tuple[int, int, int, int] | None
    elements: tuple[AIVisualElement, ...]
    raw_json: dict[str, Any]
    cache_hit: bool = False
    api_calls: int = 0
    error: str | None = None


class AIVisualStructureObserver:
    """AI-assisted visual observer with local-first cost controls.

    Default mode is dry/off: no network call is made unless
    WH_AI_VISION_ENABLED=1. The caller supplies a local analysis rectangle so
    we can send only the relevant construction crop instead of the whole screen.
    """

    MODEL_ENV = "WH_AI_VISION_MODEL"
    ENABLE_ENV = "WH_AI_VISION_ENABLED"
    MIN_CONF_ENV = "WH_AI_VISION_MIN_CONFIDENCE"
    CACHE_ENV = "WH_AI_VISION_CACHE_DIR"
    MIN_INTERVAL_ENV = "WH_AI_VISION_MIN_INTERVAL_SEC"
    API_KEY_ENV = "OPENAI_API_KEY"
    DEFAULT_MODEL = "gpt-5.6-luna"
    DEFAULT_MIN_CONFIDENCE = 0.78
    DEFAULT_MIN_INTERVAL = 1.5

    def observe(
        self,
        image: np.ndarray,
        analysis_rect: tuple[int, int, int, int] | None,
        *,
        local_confidence: float = 0.0,
        force_ai: bool = False,
    ) -> AIVisualObservation:
        if image is None or image.size == 0:
            return AIVisualObservation("EMPTY", 0.0, analysis_rect, (), {}, error="empty image")

        rect = self._clamp_rect(analysis_rect, image.shape[1], image.shape[0]) if analysis_rect else (0, 0, image.shape[1], image.shape[0])
        crop = image[rect[1] : rect[1] + rect[3], rect[0] : rect[0] + rect[2]]
        if crop.size == 0:
            return AIVisualObservation("EMPTY", 0.0, rect, (), {}, error="empty analysis crop")

        enabled = os.getenv(self.ENABLE_ENV, "0") == "1"
        min_conf = float(os.getenv(self.MIN_CONF_ENV, str(self.DEFAULT_MIN_CONFIDENCE)))
        if not force_ai and local_confidence >= min_conf:
            return AIVisualObservation("LOCAL_CONFIDENT", local_confidence, rect, (), {}, cache_hit=False, api_calls=0)

        image_bytes = self._encode_png(crop, max_side=768)
        digest = hashlib.sha256(image_bytes).hexdigest()
        cached = self._load_cache(digest)
        if cached is not None:
            return self._from_payload(cached, rect, cache_hit=True, api_calls=0)

        if not enabled:
            payload = self._build_payload_preview(rect, digest)
            return AIVisualObservation("AI_DISABLED", local_confidence, rect, (), payload, cache_hit=False, api_calls=0)

        api_key = os.getenv(self.API_KEY_ENV, "").strip()
        if not api_key:
            return AIVisualObservation("AI_NOT_CONFIGURED", local_confidence, rect, (), {}, error="OPENAI_API_KEY is not set")

        self._throttle()
        try:
            payload = self._call_openai(image_bytes, api_key)
        except Exception as exc:  # noqa: BLE001 - surface provider failure without crashing the agent
            return AIVisualObservation("AI_ERROR", local_confidence, rect, (), {}, error=str(exc))

        self._save_cache(digest, payload)
        return self._from_payload(payload, rect, cache_hit=False, api_calls=1)

    def _call_openai(self, image_bytes: bytes, api_key: str) -> dict[str, Any]:
        model = os.getenv(self.MODEL_ENV, self.DEFAULT_MODEL)
        data_url = "data:image/png;base64," + base64.b64encode(image_bytes).decode("ascii")
        schema = self._schema()
        body = {
            "model": model,
            "input": [
                {
                    "role": "developer",
                    "content": [
                        {
                            "type": "input_text",
                            "text": (
                                "You are WindowHub AI Vision. Analyze only the supplied construction screenshot. "
                                "Do not invent hidden elements. Return the visible window structure with geometry. "
                                "Use normalized element kinds FRAME, MULLION, SASH, GLASS, HARDWARE. "
                                "A cell is represented by a MULLION boundary plus its owning sash when visually supported. "
                                "Prefer null over guessing. Confidence is 0..1."
                            ),
                        }
                    ],
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": "Identify the current visible window construction and its element relationships.",
                        },
                        {"type": "input_image", "image_url": data_url, "detail": "low"},
                    ],
                },
            ],
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": "window_visual_observation",
                    "strict": True,
                    "schema": schema,
                }
            },
            "max_output_tokens": 700,
        }
        request = urllib.request.Request(
            "https://api.openai.com/v1/responses",
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                raw = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"OpenAI HTTP {exc.code}: {detail[:600]}") from exc
        payload = json.loads(raw)
        text = self._extract_output_text(payload)
        if not text:
            raise RuntimeError("OpenAI response did not contain structured output text")
        return json.loads(text)

    @staticmethod
    def _extract_output_text(payload: dict[str, Any]) -> str | None:
        if isinstance(payload.get("output_text"), str):
            return payload["output_text"]
        for item in payload.get("output", []):
            for content in item.get("content", []) if isinstance(item, dict) else []:
                if isinstance(content, dict) and isinstance(content.get("text"), str):
                    return content["text"]
        return None

    @classmethod
    def _from_payload(
        cls,
        payload: dict[str, Any],
        rect: tuple[int, int, int, int],
        *,
        cache_hit: bool,
        api_calls: int,
    ) -> AIVisualObservation:
        elements: list[AIVisualElement] = []
        for item in payload.get("elements", []):
            bbox = item.get("bbox")
            normalized_bbox = None
            if isinstance(bbox, list) and len(bbox) == 4:
                normalized_bbox = tuple(int(v) for v in bbox)
            elements.append(
                AIVisualElement(
                    id=str(item.get("id", "unknown")),
                    kind=str(item.get("kind", "UNKNOWN")),
                    side=item.get("side"),
                    parent_id=item.get("parent_id"),
                    bbox=normalized_bbox,
                    confidence=float(item.get("confidence", 0.0)),
                    properties=dict(item.get("properties", {})),
                )
            )
        return AIVisualObservation(
            status="AI_OK",
            confidence=float(payload.get("confidence", 0.0)),
            analysis_rect=rect,
            elements=tuple(elements),
            raw_json=payload,
            cache_hit=cache_hit,
            api_calls=api_calls,
        )

    @staticmethod
    def _build_payload_preview(rect: tuple[int, int, int, int], digest: str) -> dict[str, Any]:
        return {
            "mode": "dry-run",
            "analysis_rect": rect,
            "image_sha256": digest,
            "would_call": "POST /v1/responses with input_image + strict json_schema",
        }

    @classmethod
    def _schema(cls) -> dict[str, Any]:
        return {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "confidence": {"type": "number"},
                "construction_visible": {"type": "boolean"},
                "elements": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "id": {"type": "string"},
                            "kind": {"type": "string", "enum": ["FRAME", "MULLION", "SASH", "GLASS", "HARDWARE"]},
                            "side": {"type": ["string", "null"], "enum": ["left", "right", "top", "bottom", "center", None]},
                            "parent_id": {"type": ["string", "null"]},
                            "bbox": {"type": ["array", "null"], "items": {"type": "integer"}, "minItems": 4, "maxItems": 4},
                            "confidence": {"type": "number"},
                            "properties": {"type": "object", "additionalProperties": True},
                        },
                        "required": ["id", "kind", "side", "parent_id", "bbox", "confidence", "properties"],
                    },
                },
            },
            "required": ["confidence", "construction_visible", "elements"],
        }

    @staticmethod
    def _encode_png(image: np.ndarray, max_side: int) -> bytes:
        bgr = image
        if image.ndim == 2:
            bgr = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
        elif image.shape[2] == 4:
            bgr = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)
        h, w = bgr.shape[:2]
        scale = min(1.0, max_side / float(max(h, w)))
        if scale < 1.0:
            bgr = cv2.resize(bgr, (max(1, int(w * scale)), max(1, int(h * scale))), interpolation=cv2.INTER_AREA)
        ok, encoded = cv2.imencode(".png", bgr, [cv2.IMWRITE_PNG_COMPRESSION, 6])
        if not ok:
            raise RuntimeError("Could not encode vision crop")
        return encoded.tobytes()

    @classmethod
    def _cache_dir(cls) -> Path:
        return Path(os.getenv(cls.CACHE_ENV, "outputs/vision_cache"))

    @classmethod
    def _load_cache(cls, digest: str) -> dict[str, Any] | None:
        path = cls._cache_dir() / f"{digest}.json"
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None

    @classmethod
    def _save_cache(cls, digest: str, payload: dict[str, Any]) -> None:
        directory = cls._cache_dir()
        directory.mkdir(parents=True, exist_ok=True)
        (directory / f"{digest}.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    @classmethod
    def _throttle(cls) -> None:
        min_interval = float(os.getenv(cls.MIN_INTERVAL_ENV, str(cls.DEFAULT_MIN_INTERVAL)))
        stamp = cls._cache_dir() / ".last_ai_call"
        try:
            previous = float(stamp.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            previous = 0.0
        wait = min_interval - (time.time() - previous)
        if wait > 0:
            time.sleep(wait)
        stamp.parent.mkdir(parents=True, exist_ok=True)
        stamp.write_text(str(time.time()), encoding="utf-8")

    @staticmethod
    def _clamp_rect(rect: tuple[int, int, int, int] | None, width: int, height: int) -> tuple[int, int, int, int]:
        if rect is None:
            return 0, 0, width, height
        x, y, w, h = map(int, rect)
        w = max(1, min(w, width))
        h = max(1, min(h, height))
        x = max(0, min(x, width - w))
        y = max(0, min(y, height - h))
        return x, y, w, h
