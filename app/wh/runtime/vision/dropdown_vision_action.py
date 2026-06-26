from dataclasses import (
    dataclass
)


@dataclass
class DropdownVisionAction:

    name: str

    template_path: str

    value: str