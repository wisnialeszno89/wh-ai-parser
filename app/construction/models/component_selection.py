from dataclasses import dataclass


@dataclass
class ComponentSelection:

    category: str

    database_key: str

    display_name: str | None = None