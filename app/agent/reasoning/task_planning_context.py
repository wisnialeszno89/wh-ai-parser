from dataclasses import dataclass


@dataclass(frozen=True)
class TaskPlanningContext:
    """
    Model-facing context for initial task planning.

    This context is intentionally semantic. It contains no:
    - coordinates
    - window handles
    - runtime/provider identifiers
    - executor objects
    - raw perception internals
    """

    request_message: str

    intent: str

    capability_name: str | None = None

    capability_description: str | None = None

    skill_name: str | None = None

    skill_description: str | None = None

    def to_payload(
        self,
    ) -> dict[str, object]:
        return {
            "request_message": self.request_message,
            "intent": self.intent,
            "capability": (
                {
                    "name": self.capability_name,
                    "description": (
                        self.capability_description
                    ),
                }
                if self.capability_name is not None
                else None
            ),
            "skill": (
                {
                    "name": self.skill_name,
                    "description": (
                        self.skill_description
                    ),
                }
                if self.skill_name is not None
                else None
            ),
        }
