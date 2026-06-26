from dataclasses import dataclass


@dataclass(slots=True)
class MailEntity:

    entity_type: str

    value: str

    confidence: float = 1.0