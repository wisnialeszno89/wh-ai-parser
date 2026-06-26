from dataclasses import (
    dataclass
)


@dataclass
class CustomerRecognitionResult:

    customer_name: str

    recognized: bool