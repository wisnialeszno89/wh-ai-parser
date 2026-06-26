from dataclasses import dataclass, field


@dataclass(slots=True)
class Customer:

    name: str = ""

    language: str = ""

    country: str = ""

    email: str = ""

    phone: str = ""

    city: str = ""

    postal_code: str = ""

    notes: list[str] = field(default_factory=list)