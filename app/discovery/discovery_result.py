from dataclasses import dataclass, field
from typing import Any


@dataclass
class DiscoveryResult:

    success: bool

    program_name: str = "Unknown"

    gui_hash: str = ""

    toolbar_band: list = field(
        default_factory=list
    )

    toolbar_map: Any = None

    semantic_tools: list = field(
        default_factory=list
    )

    diagnostics: list[str] = field(
        default_factory=list
    )