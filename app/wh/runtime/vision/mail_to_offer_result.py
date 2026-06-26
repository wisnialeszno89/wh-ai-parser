from dataclasses import (
    dataclass
)


@dataclass
class MailToOfferResult:

    success: bool

    customer_name: str = ""

    offer_number: str = ""