from dataclasses import dataclass, field


@dataclass
class AgentState:
    """
    Mutable state belonging to one active agent session.

    This is deliberately small for now.
    It will later contain references to:
    - current customer
    - current offer
    - current construction
    - active workflow
    - recent decisions
    """

    active_task: str | None = None

    current_customer_id: str | None = None

    current_offer_id: str | None = None

    current_project_id: str | None = None

    notes: list[str] = field(
        default_factory=list
    )
