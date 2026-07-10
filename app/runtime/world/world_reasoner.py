from app.runtime.world.belief_state import BeliefState
from app.runtime.world.world_state import WorldState


class WorldReasoner:

    def reason(

        self,

        world: WorldState,

    ) -> BeliefState:

        beliefs = BeliefState()

        beliefs.toolbar_visible = world.toolbar_visible

        if world.active_tool == "FRAME":

            beliefs.frame_selected = True

            beliefs.set("FRAME_SELECTED")

        return beliefs