from math import hypot
from pathlib import Path

import cv2

from app.gui.enums.gui_tool import GuiTool
from app.runtime.execution.debug.debug_overlay import DebugOverlay
from app.runtime.execution.models.screen_element import ScreenElement
from app.runtime.execution.vision.runtime_vision import RuntimeVision
from app.runtime.execution.vision.vision_adapter import VisionAdapter
from app.wh.vision.opencv.opencv_adapter import OpenCVAdapter


class ToolLocator:

    MIN_TOOL_CONFIDENCE = 0.45
    SCALED_FALLBACK_MIN_CONFIDENCE = 0.30
    SCALE_FACTORS = (0.65, 0.75, 0.85, 0.95, 1.0, 1.05, 1.15, 1.25, 1.35)

    def __init__(self, context):
        self.context = context
        self.vision = RuntimeVision()
        self.adapter = VisionAdapter()
        self.debug = DebugOverlay()
        self.cv = OpenCVAdapter()

    def locate(self, tool: GuiTool) -> ScreenElement:
        print(f"[LOCATE] {tool.name}")

        if self.context.cache.screenshot is None:
            vision = self.vision.capture()
            self.context.cache.screenshot = vision
        else:
            vision = self.context.cache.screenshot
            print("[CACHE] Vision")

        if getattr(vision, "window", None) is None:
            raise RuntimeError("VisionContext does not contain WindowHub window bounds")

        self.context.window = vision.window

        if self.context.cache.objects is None:
            objects = self.adapter.scene.analyze(
                vision.screenshot,
                str(self.adapter.templates),
            )
            self.context.cache.objects = objects
        else:
            objects = self.context.cache.objects
            print("[CACHE] Objects")

        wanted = self.adapter.mapping.get(tool)
        if wanted is None:
            raise RuntimeError(f"No template mapped for {tool.name}")

        candidates = [
            obj
            for obj in objects
            if obj.name in wanted and obj.confidence >= self.MIN_TOOL_CONFIDENCE
        ]

        if not candidates:
            fallback = self._scaled_fallback(
                vision.screenshot.image,
                wanted,
                tool,
            )
            if fallback is not None:
                return fallback

            raise RuntimeError(
                f"{tool.name} not found with confidence >= {self.MIN_TOOL_CONFIDENCE:.2f}"
            )

        reference = None
        if tool != GuiTool.FRAME:
            frame_names = self.adapter.mapping.get(GuiTool.FRAME, [])
            frame_candidates = [
                obj
                for obj in objects
                if obj.name in frame_names and obj.confidence >= self.MIN_TOOL_CONFIDENCE
            ]
            if frame_candidates:
                reference = max(frame_candidates, key=lambda obj: obj.confidence)

        if reference is not None:
            print(
                f"[LOCATE] reference FRAME at=({reference.x},{reference.y}) "
                f"conf={reference.confidence:.3f}"
            )
            ref_cx = reference.x + reference.width / 2.0
            ref_cy = reference.y + reference.height / 2.0

            def score(obj):
                cx = obj.x + obj.width / 2.0
                cy = obj.y + obj.height / 2.0
                distance = hypot(cx - ref_cx, cy - ref_cy)
                proximity = 1.0 / (1.0 + distance / 200.0)
                return obj.confidence * 0.75 + proximity * 0.25

            candidates.sort(key=score, reverse=True)
        else:
            candidates.sort(key=lambda obj: obj.confidence, reverse=True)

        print(f"[LOCATE] {tool.name} candidates={len(candidates)}")
        for obj in candidates[:5]:
            print(
                f"[CANDIDATE] {obj.name} conf={obj.confidence:.3f} "
                f"at=({obj.x},{obj.y})"
            )

        obj = candidates[0]
        element = ScreenElement(
            name=tool.name,
            x=obj.x,
            y=obj.y,
            width=obj.width,
            height=obj.height,
            confidence=obj.confidence,
        )

        print(
            f"[VISION] FOUND {element.name} conf={element.confidence:.3f} "
            f"at=({element.x},{element.y})"
        )

        return element

    def _scaled_fallback(self, screenshot, wanted, tool):
        print(
            f"[LOCATE] {tool.name} standard matcher missed; "
            f"trying scaled templates"
        )

        best = None
        template_dir = Path(self.adapter.templates)

        for name in wanted:
            template_path = template_dir / name
            template = cv2.imread(str(template_path))

            if template is None:
                print(f"[LOCATE] missing template: {template_path}")
                continue

            for scale in self.SCALE_FACTORS:
                width = max(1, int(round(template.shape[1] * scale)))
                height = max(1, int(round(template.shape[0] * scale)))

                if width > screenshot.shape[1] or height > screenshot.shape[0]:
                    continue

                resized = cv2.resize(
                    template,
                    (width, height),
                    interpolation=cv2.INTER_AREA if scale < 1.0 else cv2.INTER_CUBIC,
                )

                result = self.cv.match_array(
                    screenshot,
                    resized,
                )

                print(
                    f"[SCALED] {name} scale={scale:.2f} "
                    f"conf={result.confidence:.3f} at=({result.x},{result.y})"
                )

                if best is None or result.confidence > best[0]:
                    best = (
                        result.confidence,
                        result,
                        name,
                        scale,
                    )

        if best is None or best[0] < self.SCALED_FALLBACK_MIN_CONFIDENCE:
            if best is not None:
                print(
                    f"[LOCATE] scaled best below threshold: "
                    f"{best[0]:.3f} < {self.SCALED_FALLBACK_MIN_CONFIDENCE:.2f}"
                )
            return None

        confidence, result, name, scale = best
        print(
            f"[LOCATE] scaled fallback selected {name} "
            f"scale={scale:.2f} conf={confidence:.3f} "
            f"at=({result.x},{result.y})"
        )

        return ScreenElement(
            name=tool.name,
            x=result.x,
            y=result.y,
            width=result.width,
            height=result.height,
            confidence=confidence,
        )
