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

        self.history = []

        self.retry_count = 0

        self.completed = False