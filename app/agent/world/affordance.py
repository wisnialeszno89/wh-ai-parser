from dataclasses import dataclass


@dataclass(frozen=True)
class Affordance:
    """
    Semantic operation the current world exposes.

    The affordance describes what can be done with an entity. It does not
    contain coordinates, handles, automation ids or an execution mechanism.
    """

    action_name: str
    target: str
    description: str
    confidence: float = 0.0
    reversible: bool = True
    requires_confirmation: bool = False

    def to_payload(self) -> dict[str, object]:
        return {
            "action_name": self.action_name,
            "target": self.target,
            "description": self.description,
            "confidence": self.confidence,
            "reversible": self.reversible,
            "requires_confirmation": self.requires_confirmation,
        }
