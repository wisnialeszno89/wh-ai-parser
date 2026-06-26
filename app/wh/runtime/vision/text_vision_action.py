from dataclasses import (
    dataclass
)


@dataclass
class TextVisionAction:

    name: str

    template_path: str

    value: str