from dataclasses import dataclass


@dataclass(slots=True)
class GuiExecutionState:
    """
    Runtime memory for GUI objects created or selected during execution.

    Coordinates are runtime observations, not persistent screen positions.
    They are valid only until the GUI state changes enough to invalidate them.
    """

    last_created_point: tuple[int, int] | None = None
    last_selected_point: tuple[int, int] | None = None

    # Geometry anchors for compound constructions.
    frame_point: tuple[int, int] | None = None
    mullion_point: tuple[int, int] | None = None

    # First sash/glass pair is placed on the left side of a vertical mullion,
    # the next pair on the right side.
    next_panel_side: str = "left"
