from dataclasses import dataclass, field

from app.agent.agent_intent import AgentIntent
from app.agent.agent_request import AgentRequest

from app.agent.capabilities.capability import (
    Capability,
)

from app.agent.environment.environment_observation import (
    EnvironmentObservation,
)

from app.agent.perception.screen_scene import (
    ScreenScene,
)

from app.agent.planning.action_plan import (
    ActionPlan,
)

from app.agent.skills.agent_skill import (
    AgentSkill,
)


@dataclass
class ExecutionContext:
    """
    Shared mutable execution state.

    This context is used by action executors to exchange
    controlled runtime information during plan execution.

    The context contains both:

    - generic execution data
    - the latest observed environment state
    - the latest interpreted screen scene

    The explicit perception fields prevent environment
    state from becoming hidden inside arbitrary metadata.
    """

    request: AgentRequest

    last_observation: (
        EnvironmentObservation | None
    ) = None

    current_scene: (
        ScreenScene | None
    ) = None

    data: dict[str, object] = field(
        default_factory=dict
    )

    def update_observation(
        self,
        observation: EnvironmentObservation,
    ) -> None:
        """
        Store the latest raw environment observation.
        """

        self.last_observation = observation

    def update_scene(
        self,
        scene: ScreenScene,
    ) -> None:
        """
        Store the latest interpreted screen scene.

        The scene also represents an observation,
        therefore the underlying observation becomes
        the latest observation automatically.
        """

        self.current_scene = scene

        self.last_observation = (
            scene.observation
        )

    def set_value(
        self,
        key: str,
        value: object,
    ) -> None:

        self.data[key] = value

    def get_value(
        self,
        key: str,
        default: object | None = None,
    ) -> object | None:

        return self.data.get(
            key,
            default,
        )

    def has_value(
        self,
        key: str,
    ) -> bool:

        return key in self.data

    def remove_value(
        self,
        key: str,
    ) -> object | None:

        return self.data.pop(
            key,
            None,
        )


@dataclass
class AgentExecutionContext(
    ExecutionContext
):
    """
    Rich execution context produced by the agent orchestrator.

    Extends the base execution context with semantic planning
    information required by the agent runtime.

    The context also carries the latest known perception state
    while the agent is executing.
    """

    intent: AgentIntent = (
        AgentIntent.UNKNOWN
    )

    plan: ActionPlan | None = None

    capability: Capability | None = None

    skill: AgentSkill | None = None

    requires_manual_review: bool = False
