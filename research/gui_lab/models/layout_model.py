from dataclasses import dataclass, field

from research.gui_lab.core.panel_detector import (
    Panel,
)

from research.gui_lab.extractors.panel_fingerprint import (
    PanelFingerprint,
)


@dataclass(slots=True)
class LayoutPanel:

    id: int

    panel: Panel

    fingerprint: PanelFingerprint | None = None

    semantic_role: str | None = None

    confidence: float = 0.0


@dataclass(slots=True)
class LayoutModel:

    panels: list[LayoutPanel] = field(
        default_factory=list
    )

    def add_panel(
        self,
        panel: LayoutPanel,
    ):

        self.panels.append(
            panel
        )

    def __len__(self):

        return len(
            self.panels
        )

    def __iter__(self):

        return iter(
            self.panels
        )

    def get_panel(
        self,
        panel_id: int,
    ):

        for panel in self.panels:

            if panel.id == panel_id:

                return panel

        return None