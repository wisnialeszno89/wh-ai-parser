from dataclasses import dataclass


@dataclass
class GUIAction:

    action: str

    screen: str

    control: str

    value: str