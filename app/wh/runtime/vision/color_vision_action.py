from dataclasses import (
    dataclass
)


@dataclass
class ColorVisionAction:

    name: str

    template_path: str

    color: str