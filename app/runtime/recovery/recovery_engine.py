from app.runtime.agent.agent_state import AgentState
from app.runtime.brain.recovery_type import RecoveryType
from app.runtime.world.perception_engine import PerceptionEngine


class RecoveryEngine:

    def __init__(self):

        self.perception = PerceptionEngine()

    def recover(
        self,
        state: AgentState,
        recovery: RecoveryType,
    ) -> bool:

        if recovery == RecoveryType.REFRESH_WORLD:

            state.world = self.perception.perceive()

            return True

        return False