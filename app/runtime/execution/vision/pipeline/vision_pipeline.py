from app.runtime.execution.window.window_locator import (
    WindowLocator,
)

from app.wh.vision.mss_screenshot_engine import (
    MSSScreenshotEngine,
)

from app.runtime.execution.debug.debug_overlay import (
    DebugOverlay,
)

from app.runtime.execution.debug.roi_debug import (
    ROIDebug,
)

from app.runtime.execution.vision.analyzers.legacy_toolbar_band_detector import (
    LegacyToolbarBandDetector,
)

from app.runtime.execution.vision.analyzers.section_analyzer import (
    SectionAnalyzer,
)

from app.runtime.execution.vision.analyzers.candidate_generator import (
    CandidateGenerator,
)

from app.runtime.execution.vision.analyzers.canvas_analyzer import (
    CanvasAnalyzer,
)

from app.runtime.execution.vision.analyzers.construction_analyzer import (
    ConstructionAnalyzer,
)

from app.runtime.execution.vision.roi.roi_extractor import (
    ROIExtractor,
)

from app.runtime.execution.vision.models.vision_context import (
    VisionContext,
)


class VisionPipeline:

    def __init__(self):

        self.window_locator = WindowLocator()

        self.screenshot_engine = MSSScreenshotEngine()

        self.toolbar_detector = LegacyToolbarBandDetector()

        self.canvas_analyzer = CanvasAnalyzer()

        self.construction_analyzer = ConstructionAnalyzer()

        self.section_analyzer = SectionAnalyzer()

        self.candidate_generator = CandidateGenerator()

        self.roi_extractor = ROIExtractor()

        self.debug_overlay = DebugOverlay()

        self.roi_debug = ROIDebug()

    def observe(self):

        #
        # Locate window.
        #

        window = self.window_locator.locate()

        #
        # Capture screenshot.
        #

        screenshot = self.screenshot_engine.capture(
            window,
        )

        #
        # Vision context.
        #

        context = VisionContext(
            window=window,
            screenshot=screenshot,
        )

        #
        # Toolbar.
        #

        toolbar = self.toolbar_detector.analyze(
            screenshot,
        )

        if toolbar is None:

            print("[VISION] Toolbar not found")

            return context

        context.toolbar = toolbar

        #
        # Canvas / construction.
        #

        context = self.canvas_analyzer.analyze(
            context,
        )

        context.construction = self.construction_analyzer.analyze(
            context,
        )

        #
        # Sections.
        #

        self.section_analyzer.analyze(
            screenshot,
            toolbar,
        )

        #
        # Controls.
        #

        for section in toolbar.children:

            self.candidate_generator.analyze(
                screenshot,
                section,
            )

            #
            # Save every detected ROI.
            #

            for control in section.children:

                roi = self.roi_extractor.extract(
                    screenshot,
                    control,
                )

                self.roi_debug.save(
                    roi,
                )

        #
        # Debug overlay.
        #

        self.debug_overlay.render(
            screenshot=screenshot,
            toolbar=toolbar,
            canvas=context.canvas,
        )

        return context
