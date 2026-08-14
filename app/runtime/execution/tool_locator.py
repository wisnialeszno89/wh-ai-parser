from pathlib import Path

import cv2

from app.gui.enums.gui_tool import GuiTool
from app.runtime.execution.debug.debug_overlay import DebugOverlay
from app.runtime.execution.models.screen_element import ScreenElement
from app.runtime.execution.vision.runtime_vision import RuntimeVision
from app.runtime.execution.vision.vision_adapter import VisionAdapter
from app.wh.vision.opencv.opencv_adapter import OpenCVAdapter


class ToolLocator:
    """
    Locate construction tools using both template confidence and spatial context.

    WindowHub has application-level icons in the top toolbar that can look
    similar to construction tools. The current workspace is therefore used as
    an anchor: construction tools are expected in a side tool panel adjacent
    to the workspace, not in the top application toolbar.
    """

    MIN_TOOL_CONFIDENCE = 0.45
    SCALED_FALLBACK_MIN_CONFIDENCE = 0.30
    SCALE_FACTORS = (0.65, 0.75, 0.85, 0.95, 1.0, 1.05, 1.15, 1.25, 1.35)

    PANEL_X_MARGIN = 180
    PANEL_Y_MARGIN = 220

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

        all_candidates = [
            obj
            for obj in objects
            if obj.name in wanted and obj.confidence >= self.MIN_TOOL_CONFIDENCE
        ]

        panel_candidates = self._panel_candidates(vision, all_candidates)

        if panel_candidates:
            obj = self._choose_candidate(vision, panel_candidates)
            return self._to_element(tool, obj)

        # Standard matching can miss the real icon because of DPI/scaling.
        # The scaled fallback is intentionally restricted to the construction
        # panel region so a visually similar top-toolbar icon cannot win.
        fallback = self._scaled_fallback(
            vision,
            wanted,
            tool,
        )
        if fallback is not None:
            return fallback

        if all_candidates:
            raise RuntimeError(
                f"{tool.name} matched outside the construction tool panel"
            )

        raise RuntimeError(
            f"{tool.name} not found in construction tool panel"
        )

    def _panel_candidates(self, vision, candidates):
        canvas = getattr(getattr(vision, "canvas", None), "bounds", None)
        if canvas is None:
            print("[LOCATE] No canvas anchor; spatial panel filtering disabled")
            return list(candidates)

        selected = []
        for obj in candidates:
            if self._is_panel_candidate(canvas, obj):
                selected.append(obj)
                print(
                    f"[PANEL CANDIDATE] {obj.name} conf={obj.confidence:.3f} "
                    f"at=({obj.x},{obj.y})"
                )

        print(
            f"[LOCATE] construction-panel candidates={len(selected)} "
            f"of {len(candidates)}"
        )
        return selected

    def _is_panel_candidate(self, canvas, obj) -> bool:
        cx = obj.x + obj.width / 2.0
        cy = obj.y + obj.height / 2.0

        vertical_ok = (
            canvas.top - self.PANEL_Y_MARGIN
            <= cy
            <= canvas.bottom + self.PANEL_Y_MARGIN
        )
        if not vertical_ok:
            return False

        distance_to_left_edge = abs(cx - canvas.left)
        distance_to_right_edge = abs(cx - canvas.right)

        return min(distance_to_left_edge, distance_to_right_edge) <= self.PANEL_X_MARGIN

    def _choose_candidate(self, vision, candidates):
        canvas = getattr(getattr(vision, "canvas", None), "bounds", None)
        if canvas is None:
            return max(candidates, key=lambda obj: obj.confidence)

        def score(obj):
            cx = obj.x + obj.width / 2.0
            cy = obj.y + obj.height / 2.0

            side_distance = min(
                abs(cx - canvas.left),
                abs(cx - canvas.right),
            )

            if cy < canvas.top:
                vertical_distance = canvas.top - cy
            elif cy > canvas.bottom:
                vertical_distance = cy - canvas.bottom
            else:
                vertical_distance = 0.0

            side_proximity = 1.0 / (1.0 + side_distance / 80.0)
            vertical_proximity = 1.0 / (1.0 + vertical_distance / 120.0)

            return (
                obj.confidence * 0.70
                + side_proximity * 0.20
                + vertical_proximity * 0.10
            )

        candidates.sort(key=score, reverse=True)

        print(f"[LOCATE] candidate ranking ({len(candidates)})")
        for obj in candidates[:5]:
            print(
                f"[CANDIDATE] {obj.name} conf={obj.confidence:.3f} "
                f"at=({obj.x},{obj.y}) score={score(obj):.3f}"
            )

        return candidates[0]

    def _to_element(self, tool, obj):
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

    def _scaled_fallback(self, vision, wanted, tool):
        canvas = getattr(getattr(vision, "canvas", None), "bounds", None)
        if canvas is None:
            print(
                f"[LOCATE] {tool.name} scaled fallback skipped: no canvas anchor"
            )
            return None

        screenshot = vision.screenshot.image

        x1 = max(0, canvas.left - self.PANEL_X_MARGIN)
        x2 = min(screenshot.shape[1], canvas.right + self.PANEL_X_MARGIN)
        y1 = max(0, canvas.top - self.PANEL_Y_MARGIN)
        y2 = min(screenshot.shape[0], canvas.bottom + self.PANEL_Y_MARGIN)

        region = screenshot[y1:y2, x1:x2]
        if region.size == 0:
            return None

        print(
            f"[LOCATE] {tool.name} scaled fallback in panel region "
            f"({x1},{y1})-({x2},{y2})"
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

                if width > region.shape[1] or height > region.shape[0]:
                    continue

                resized = cv2.resize(
                    template,
                    (width, height),
                    interpolation=cv2.INTER_AREA if scale < 1.0 else cv2.INTER_CUBIC,
                )

                result = self.cv.match_array(
                    region,
                    resized,
                )

                absolute_x = x1 + result.x
                absolute_y = y1 + result.y

                print(
                    f"[SCALED] {name} scale={scale:.2f} "
                    f"conf={result.confidence:.3f} "
                    f"at=({absolute_x},{absolute_y})"
                )

                candidate = (
                    result.confidence,
                    absolute_x,
                    absolute_y,
                    result.width,
                    result.height,
                    name,
                    scale,
                )

                if best is None or result.confidence > best[0]:
                    best = candidate

        if best is None or best[0] < self.SCALED_FALLBACK_MIN_CONFIDENCE:
            if best is not None:
                print(
                    f"[LOCATE] scaled best below threshold: "
                    f"{best[0]:.3f} < {self.SCALED_FALLBACK_MIN_CONFIDENCE:.2f}"
                )
            return None

        confidence, x, y, width, height, name, scale = best
        print(
            f"[LOCATE] scaled fallback selected {name} "
            f"scale={scale:.2f} conf={confidence:.3f} "
            f"at=({x},{y})"
        )

        return ScreenElement(
            name=tool.name,
            x=x,
            y=y,
            width=width,
            height=height,
            confidence=confidence,
        )
