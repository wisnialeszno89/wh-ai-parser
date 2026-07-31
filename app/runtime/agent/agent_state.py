from app.runtime.mission.mission import Mission
from app.runtime.world.world_state import WorldState


class AgentState:

    def __init__(
        self,
        mission: Mission,
    ):
        self.mission = mission

        self.current_step = 0

        self.last_action = None

        self.last_result = None

        self.current_screen = None

        self.world = WorldState()

        self.screen_objects = []

        self.retry_count = 0

        self.completed = False

    @property
    def can_retry(
        self,
    ) -> bool:

        return (
            self.retry_count
            < self.mission.retry_limit
        )

    def increment_retry(
        self,
    ) -> None:

        self.retry_count += 1

    def reset_retry(
        self,
    ) -> None:

        self.retry_count = 0

    def next_step(
        self,
    ) -> None:

        self.current_step += 1

    def finish(
        self,
    ) -> None:

        self.completed = True