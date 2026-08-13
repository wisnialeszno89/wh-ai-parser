from math import hypot

from app.gui.enums.gui_tool import GuiTool
from app.runtime.execution.debug.debug_overlay import DebugOverlay
from app.runtime.execution.models.screen_element import ScreenElement
from app.runtime.execution.vision.runtime_vision import RuntimeVision
from app.runtime.execution.vision.vision_adapter import VisionAdapter


class ToolLocator:

    MIN_TOOL_CONFIDENCE = 0.45

    def __init__(self, context):
        self.context = context
        self.vision = RuntimeVision()
        self.adapter = VisionAdapter()
        self.debug = DebugOverlay()

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
