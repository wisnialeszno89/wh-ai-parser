from dataclasses import dataclass, field

from app.wh.domain.customer.customer import Customer
from app.wh.domain.product.product_request import ProductRequest


@dataclass(slots=True)
class CustomerRequest:

    customer: Customer

    products: list[ProductRequest] = field(default_factory=list)

    installation: bool = False

    transport: bool = False

    language: str = ""

    notes: list[str] = field(default_factory=list)

    attachments: list[str] = field(default_factory=list)