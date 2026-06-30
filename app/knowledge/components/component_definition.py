from dataclasses import dataclass


@dataclass
class ComponentDefinition:

    profile: str

    default_frame: str

    default_glass: str

    default_hardware: str

    default_extension: str | None = None