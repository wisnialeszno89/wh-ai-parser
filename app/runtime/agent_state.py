from dataclasses import dataclass


@dataclass
class AgentState:

    current_profile: str | None = None

    current_color: str | None = None

    current_position: int = 0

    completed_positions: int = 0

    review_positions: list[int] = None

    def __post_init__(self):

        if self.review_positions is None:

            self.review_positions = []