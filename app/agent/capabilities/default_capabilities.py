from app.agent.capabilities.capability import Capability
from app.agent.capabilities.capability_registry import (
    CapabilityRegistry,
)


WH_WINDOW = Capability(
    name="WH_WINDOW",
    description=(
        "Technical window construction, "
        "quotation workflows and controlled "
        "execution in WH."
    ),
)


EXCEL = Capability(
    name="EXCEL",
    description=(
        "Spreadsheet analysis, editing, "
        "data processing and office workflows."
    ),
)


COMPUTER_USE = Capability(
    name="COMPUTER_USE",
    description=(
        "Universal semantic computer-use capability: observe the current "
        "environment, choose safe semantic UI actions and verify results."
    ),
)


WORD = Capability(
    name="WORD",
    description=(
        "Document creation, editing and "
        "office document workflows."
    ),
)


def create_default_capability_registry(
) -> CapabilityRegistry:
    return CapabilityRegistry(
        capabilities=(
            WH_WINDOW,
            COMPUTER_USE,
            EXCEL,
            WORD,
        )
    )
