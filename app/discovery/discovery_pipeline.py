from app.discovery.discovery_result import DiscoveryResult

from app.ui.runtime.gui_detector import (
    GuiDetector
)

class DiscoveryPipeline:

    def run(
        self,
        image
    ) -> DiscoveryResult:

        print()
        print("===================================")
        print(" Universal Discovery Pipeline")
        print("===================================")
        print()

        detector = GuiDetector()

        gui = detector.detect(
    image
)

        toolbar_band = gui.toolbar_band

        print(
            f"✓ Toolbar candidates: {len(toolbar_band)}"
        )

        self.find_tools()

        self.classify_tools()

        self.build_gui_map()

        print()
        print("Discovery finished.")
        print()

        return DiscoveryResult(

            success=True,

            toolbar_band=toolbar_band,

            diagnostics=[

                "Pipeline executed."

            ]

        )

    def find_tools(self):

        print("• Detect tools")

    def classify_tools(self):

        print("• Classify semantic tools")

    def build_gui_map(self):

        print("• Build GUI map")