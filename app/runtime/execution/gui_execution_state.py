from dataclasses import dataclass, field


@dataclass(slots=True)
class GuiExecutionState:
    """
    Runtime memory for GUI objects created or selected during execution.

    Coordinates are runtime observations, not persistent screen positions.
    """

    last_created_point: tuple[int, int] | None = None
    last_selected_point: tuple[int, int] | None = None

    # Geometry anchors for compound constructions.
    frame_point: tuple[int, int] | None = None
    sash_point: tuple[int, int] | None = None
    glass_point: tuple[int, int] | None = None
    mullion_point: tuple[int, int] | None = None
    workspace_bounds: tuple[int, int, int, int] | None = None

    # Orientation of the current divider.
    mullion_orientation: str | None = None

    # Last successfully resolved tool positions. These are runtime anchors,
    # not fixed screen coordinates.
    tool_points: dict[str, tuple[int, int]] = field(default_factory=dict)

    # Current construction cell used by the SASH + GLASS pair.
    # Vertical mullion: left/right. Horizontal mullion: top/bottom.
    panel_side: str = "left"
    panel_pair_point: tuple[int, int] | None = None
    last_panel_component: str | None = None
