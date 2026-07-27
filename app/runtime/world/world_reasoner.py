from app.runtime.world.belief_state import BeliefState
from app.runtime.world.world_state import WorldState


class WorldReasoner:

    def reason(
        self,
        world: WorldState,
    ) -> BeliefState:

        beliefs = BeliefState()

        #
        # Możemy wykonywać akcje.
        #

        beliefs.can_execute_actions = (
            world.toolbar_visible
        )

        #
        # Aktualnie aktywne narzędzie FRAME.
        #

        beliefs.frame_mode_active = (
            world.active_tool == "FRAME"
        )

        #
        # Na razie jeszcze nie analizujemy dialogów.
        #

        beliefs.interaction_blocked = False

        #
        # Na razie brak detekcji błędów.
        #

        beliefs.error_detected = False

        return beliefs