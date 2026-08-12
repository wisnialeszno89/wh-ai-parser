from app.runtime.mission.mission import Mission
from app.runtime.mission.mission_trace import MissionTrace
from app.runtime.world.world_state import WorldState

from app.runtime.memory.action_memory import ActionMemory


class AgentState:
    """
    Holds the runtime state of the autonomous agent while executing a mission.

    This state is engine-level and should remain independent of any
    domain-specific implementation (WindowHub, LinkedIn, Indeed, etc.).
    """

    def __init__(
        self,
        mission: Mission,
    ):

        self.mission = mission

        #
        # Mission execution
        #

        self.current_step = 0

        self.completed = False

        #
        # Current action
        #

        self.last_action = None

        self.last_result = None

        #
        # World model
        #

        self.world = WorldState()

        self.current_screen = None

        self.screen_objects = []

        #
        # Retry state
        #

        self.retry_count = 0

        #
        # Mission trace
        #

        self.trace = MissionTrace()

        #
        # Runtime action memory
        #

        self.action_memory: dict[str, ActionMemory] = {}

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

    def memory_for(
        self,
        action_name: str,
    ) -> ActionMemory:

        memory = self.action_memory.get(action_name)

        if memory is None:

            memory = ActionMemory()

            self.action_memory[action_name] = memory

        return memory