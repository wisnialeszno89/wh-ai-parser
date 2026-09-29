from enum import Enum


class InteractionCapability(str, Enum):
    """
    Generic interaction capability inferred for a visible screen element.

    Visual type and interaction capability are intentionally separate:
    an element may look like an ICON without providing evidence that it
    is safely clickable, while a BUTTON can currently provide explicit
    click capability.
    """

    UNKNOWN = "unknown"
    NOT_INTERACTIVE = "not_interactive"
    CLICKABLE = "clickable"
