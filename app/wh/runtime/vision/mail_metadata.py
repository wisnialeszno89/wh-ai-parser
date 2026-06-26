from dataclasses import (
    dataclass
)


@dataclass
class MailMetadata:

    sender_email: str = ""

    sender_name: str = ""

    company: str = ""

    language: str = ""

    priority: str = "normal"

    request_type: str = "unknown"