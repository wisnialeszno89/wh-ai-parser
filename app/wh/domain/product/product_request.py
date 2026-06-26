from dataclasses import dataclass


@dataclass(slots=True)
class ProductRequest:

    category: str

    quantity: int = 1

    width: int | None = None

    height: int | None = None

    opening_type: str | None = None

    outside_color: str | None = None

    inside_color: str | None = None

    glazing: str | None = None

    security: str | None = None

    profile: str | None = None