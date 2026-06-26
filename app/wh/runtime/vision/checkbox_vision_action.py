from dataclasses import (
    dataclass
)


@dataclass
class CheckboxVisionAction:

    name: str

    template_path: str

    checked: bool = True