from dataclasses import dataclass, field

from app.wh.runtime.vision.products.window_product import (
    WindowProduct
)


@dataclass(slots=True)
class OfferSpecification:

    customer_name: str = ""

    language: str = ""

    products: list[WindowProduct] = field(

        default_factory=list

    )

    installation: bool = False

    transport: bool = False

    notes: str = ""