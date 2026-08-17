from math import hypot
from pathlib import Path

import cv2

from app.gui.enums.gui_tool import GuiTool
from app.runtime.execution.debug.debug_overlay import DebugOverlay
from app.runtime.execution.hardware_icon_template import load_hardware_icon_template
from app.runtime.execution.models.screen_element import ScreenElement
from app.runtime.execution.vision.runtime_vision import RuntimeVision
from app.runtime.execution.vision.vision_adapter import VisionAdapter
from app.wh.vision.opencv.opencv_adapter import OpenCVAdapter


class ToolLocator:
    MIN_TOOL_CONFIDENCE = 0.45
    SCALED_FALLBACK_MIN_CONFIDENCE = 0.22
    SCALE_FACTORS = (
        0.16,
        0.20,
        0.24,
        0.28,
        0.32,
        0.40,
        0.50,
        0.65,
        0.75,
        0.85,
        0.95,
        1.0,
        1.05,
        1.15,
        1.25,
        1.35,
    )
    HARDWARE_SCALE_FACTORS = (0.75, 0.85, 0.95, 1.0, 1.05, 1.15, 1.25, 1.4)
    PANEL_X_MARGIN = 55
    PANEL_Y_MARGIN = 420
    TOOL_ANCHOR_X_MARGIN = 70
    TOOL_ANCHOR_Y_MARGIN = 90
    HARDWARE_TOOLBAR_MAX_X = 150
    HARDWARE_MIN_CONFIDENCE = 0.82

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
            raise RuntimeError(
                "VisionContext does not contain WindowHub window bounds"
            )
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

        if tool == GuiTool.HARDWARE:
            return self._locate_hardware_toolbar(vision)

        # Once a tool has been located successfully, its own runtime position
        # is the strongest reference for locating the same tool again. This is
        # especially important for repeated SASH actions: a later screenshot
        # can contain visually similar icons (for example insect screens), and
        # global template matching alone may otherwise choose the wrong one.
        tool_anchor = self.context.gui_state.tool_points.get(tool.name)
        if tool_anchor is not None:
            print(
                f"[LOCATE] runtime anchor {tool.name} at="
                f"({tool_anchor[0]},{tool_anchor[1]})"
            )

        reference = None
        if tool != GuiTool.FRAME and tool_anchor is None:
            frame_names = self.adapter.mapping.get(GuiTool.FRAME, [])
            frame_candidates = [
                obj
                for obj in objects
                if obj.name in frame_names
                and obj.confidence >= self.MIN_TOOL_CONFIDENCE
            ]
            if frame_candidates:
                reference = max(
                    frame_candidates,
                    key=lambda obj: obj.confidence,
                )
                print(
                    f"[LOCATE] reference FRAME at=({reference.x},{reference.y}) "
                    f"conf={reference.confidence:.3f}"
                )

        if tool == GuiTool.FRAME:
            candidates = [
                obj
                for obj in objects
                if obj.name in wanted
                and obj.confidence >= self.MIN_TOOL_CONFIDENCE
            ]
        elif tool_anchor is not None:
            candidates = [
                obj
                for obj in objects
                if obj.name in wanted
                and obj.confidence >= self.MIN_TOOL_CONFIDENCE
                and self._near_tool_anchor(tool_anchor, obj, vision.screenshot)
            ]
        elif reference is not None:
            candidates = [
                obj
                for obj in objects
                if obj.name in wanted
                and obj.confidence >= self.MIN_TOOL_CONFIDENCE
                and self._same_construction_column(
                    reference,
                    obj,
                    vision.screenshot,
                )
            ]
        else:
            candidates = []

        if candidates:
            candidates.sort(
                key=self._candidate_score(tool_anchor, reference),
                reverse=True,
            )
            for obj in candidates[:5]:
                print(
                    f"[CANDIDATE] {obj.name} conf={obj.confidence:.3f} "
                    f"at=({obj.x},{obj.y})"
                )
            return self._remember_tool(tool, candidates[0])

        fallback = self._scaled_fallback(
            vision,
            wanted,
            tool,
            tool_anchor,
            reference,
        )
        if fallback is not None:
            return self._remember_element(tool, fallback)

        raise RuntimeError(
            f"{tool.name} not found in construction tool panel"
        )

    def _locate_hardware_toolbar(self, vision) -> ScreenElement:
        """Locate the real Okucia button from the left vertical toolbar.

        HARDWARE is intentionally isolated from the generic construction-panel
        matcher. The user-provided crop is an exact 24x28 sample of the active
        WindowHub button, so searching the left toolbar gives us a much stronger
        signal than guessing from visually similar construction icons.
        """
        screenshot = vision.screenshot.image
        toolbar_width = min(self.HARDWARE_TOOLBAR_MAX_X, screenshot.shape[1])
        region = screenshot[:, :toolbar_width]
        template = load_hardware_icon_template()

        best = None
        print(
            f"[HARDWARE] exact toolbar search x=0..{toolbar_width} "
            f"scales={self.HARDWARE_SCALE_FACTORS}"
        )

        for scale in self.HARDWARE_SCALE_FACTORS:
            width = max(1, int(round(template.shape[1] * scale)))
            height = max(1, int(round(template.shape[0] * scale)))
            if width > region.shape[1] or height > region.shape[0]:
                continue

            resized = cv2.resize(
                template,
                (width, height),
                interpolation=(
                    cv2.INTER_AREA if scale < 1.0 else cv2.INTER_CUBIC
                ),
            )
            result = self.cv.match_array(region, resized)
            center_x = result.x + result.width / 2.0
            center_y = result.y + result.height / 2.0

            # Exclude the very top utility toolbar; the hardware button lives
            # on the left construction toolbar below the main menus.
            if center_y < 90:
                continue

            print(
                f"[HARDWARE] scale={scale:.2f} conf={result.confidence:.3f} "
                f"at=({result.x},{result.y})"
            )

            candidate = (
                result.confidence,
                result.x,
                result.y,
                result.width,
                result.height,
                scale,
            )
            if best is None or result.confidence > best[0]:
                best = candidate

        if best is None or best[0] < self.HARDWARE_MIN_CONFIDENCE:
            score = 0.0 if best is None else best[0]
            print(
                f"[HARDWARE] exact toolbar match below threshold: "
                f"{score:.3f} < {self.HARDWARE_MIN_CONFIDENCE:.2f}"
            )
            raise RuntimeError(
                "HARDWARE not found: exact Okucia toolbar button was not detected"
            )

        confidence, x, y, width, height, scale = best
        element = ScreenElement(
            name=GuiTool.HARDWARE.name,
            x=int(x),
            y=int(y),
            width=int(width),
            height=int(height),
            confidence=float(confidence),
        )
        print(
            f"[HARDWARE] FOUND exact Okucia button "
            f"conf={confidence:.3f} scale={scale:.2f} "
            f"at=({x},{y})"
        )
        return self._remember_element(GuiTool.HARDWARE, element)

    def _near_tool_anchor(self, anchor, obj, screenshot) -> bool:
        anchor_x, anchor_y = anchor
        obj_cx = obj.x + obj.width / 2.0
        obj_cy = obj.y + obj.height / 2.0
        return (
            abs(obj_cx - anchor_x) <= self.TOOL_ANCHOR_X_MARGIN
            and abs(obj_cy - anchor_y) <= self.TOOL_ANCHOR_Y_MARGIN
            and obj.x >= 0
            and obj.y >= 0
            and obj.x + obj.width <= screenshot.shape[1]
            and obj.y + obj.height <= screenshot.shape[0]
        )

    def _same_construction_column(self, reference, obj, screenshot) -> bool:
        ref_cx = reference.x + reference.width / 2.0
        ref_cy = reference.y + reference.height / 2.0
        obj_cx = obj.x + obj.width / 2.0
        obj_cy = obj.y + obj.height / 2.0
        return (
            abs(obj_cx - ref_cx) <= self.PANEL_X_MARGIN
            and abs(obj_cy - ref_cy) <= self.PANEL_Y_MARGIN
            and obj.x >= 0
            and obj.y >= 0
            and obj.x + obj.width <= screenshot.shape[1]
            and obj.y + obj.height <= screenshot.shape[0]
        )

    def _candidate_score(self, anchor, reference):
        if anchor is not None:
            anchor_x, anchor_y = anchor

            def score(obj):
                cx = obj.x + obj.width / 2.0
                cy = obj.y + obj.height / 2.0
                distance = hypot(cx - anchor_x, cy - anchor_y)
                return (
                    obj.confidence * 0.75
                    + (1.0 / (1.0 + distance / 80.0)) * 0.25
                )

            return score

        if reference is None:
            return lambda obj: obj.confidence

        ref_cx = reference.x + reference.width / 2.0
        ref_cy = reference.y + reference.height / 2.0

        def score(obj):
            cx = obj.x + obj.width / 2.0
            cy = obj.y + obj.height / 2.0
            distance = hypot(cx - ref_cx, cy - ref_cy)
            return (
                obj.confidence * 0.8
                + (1.0 / (1.0 + distance / 120.0)) * 0.2
            )

        return score

    def _to_element(self, tool, obj):
        return ScreenElement(
            name=tool.name,
            x=obj.x,
            y=obj.y,
            width=obj.width,
            height=obj.height,
            confidence=obj.confidence,
        )

    def _remember_tool(self, tool, obj):
        element = self._to_element(tool, obj)
        center = (
            element.x + element.width / 2.0,
            element.y + element.height / 2.0,
        )
        self.context.gui_state.tool_points[tool.name] = (
            int(round(center[0])),
            int(round(center[1])),
        )
        print(
            f"[VISION] FOUND {element.name} conf={element.confidence:.3f} "
            f"at=({element.x},{element.y}) "
            f"anchor={self.context.gui_state.tool_points[tool.name]}"
        )
        return element

    def _remember_element(self, tool, element):
        self.context.gui_state.tool_points[tool.name] = (
            int(round(element.x + element.width / 2.0)),
            int(round(element.y + element.height / 2.0)),
        )
        print(
            f"[VISION] FOUND {element.name} conf={element.confidence:.3f} "
            f"at=({element.x},{element.y}) "
            f"anchor={self.context.gui_state.tool_points[tool.name]}"
        )
        return element

    def _scaled_fallback(
        self,
        vision,
        wanted,
        tool,
        tool_anchor,
        reference,
    ):
        if tool_anchor is not None:
            ref_cx = int(round(tool_anchor[0]))
            ref_cy = int(round(tool_anchor[1]))
        elif reference is not None:
            ref_cx = int(round(reference.x + reference.width / 2.0))
            ref_cy = int(round(reference.y + reference.height / 2.0))
        else:
            return None

        screenshot = vision.screenshot.image
        half_width = int(
            max(
                45,
                reference.width * 2.0 if reference is not None else 90,
            )
        )
        x1 = max(0, ref_cx - half_width)
        x2 = min(screenshot.shape[1], ref_cx + half_width)
        y1 = max(
            0,
            ref_cy - (self.TOOL_ANCHOR_Y_MARGIN if tool_anchor else self.PANEL_Y_MARGIN),
        )
        y2 = min(
            screenshot.shape[0],
            ref_cy + (self.TOOL_ANCHOR_Y_MARGIN if tool_anchor else self.PANEL_Y_MARGIN),
        )
        region = screenshot[y1:y2, x1:x2]
        if region.size == 0:
            return None

        print(
            f"[LOCATE] {tool.name} scaled fallback in construction column "
            f"({x1},{y1})-({x2},{y2})"
        )
        best = None
        template_dir = Path(self.adapter.templates)
        for name in wanted:
            template = cv2.imread(str(template_dir / name))
            if template is None:
                continue
            for scale in self.SCALE_FACTORS:
                width = max(1, int(round(template.shape[1] * scale)))
                height = max(1, int(round(template.shape[0] * scale)))
                if width > region.shape[1] or height > region.shape[0]:
                    continue
                resized = cv2.resize(
                    template,
                    (width, height),
                    interpolation=(
                        cv2.INTER_AREA if scale < 1.0 else cv2.INTER_CUBIC
                    ),
                )
                result = self.cv.match_array(region, resized)
                absolute_x = x1 + result.x
                absolute_y = y1 + result.y
                candidate_cx = absolute_x + result.width / 2.0
                candidate_cy = absolute_y + result.height / 2.0

                if tool_anchor is not None:
                    valid = (
                        abs(candidate_cx - ref_cx) <= self.TOOL_ANCHOR_X_MARGIN
                        and abs(candidate_cy - ref_cy) <= self.TOOL_ANCHOR_Y_MARGIN
                    )
                else:
                    valid = (
                        abs(candidate_cx - ref_cx) <= self.PANEL_X_MARGIN
                        and abs(candidate_cy - ref_cy) <= self.PANEL_Y_MARGIN
                    )
                if not valid:
                    continue

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

        if best is None:
            return None

        confidence, x, y, width, height, name, scale = best
        if confidence < self.SCALED_FALLBACK_MIN_CONFIDENCE:
            print(
                f"[LOCATE] construction-column best below threshold: "
                f"{confidence:.3f} < {self.SCALED_FALLBACK_MIN_CONFIDENCE:.2f}"
            )
            return None

        print(
            f"[LOCATE] scaled fallback selected {name} scale={scale:.2f} "
            f"conf={confidence:.3f} at=({x},{y})"
        )
        return ScreenElement(
            name=tool.name,
            x=x,
            y=y,
            width=width,
            height=height,
            confidence=confidence,
        )
