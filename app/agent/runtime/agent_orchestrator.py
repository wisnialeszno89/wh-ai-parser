from app.agent.agent_intent import AgentIntent
from app.agent.agent_request import AgentRequest

from app.agent.capabilities.capability_router import (
    CapabilityRouter,
)

from app.agent.capabilities.default_capabilities import (
    create_default_capability_registry,
)

from app.agent.planning.agent_planner import (
    AgentPlanner,
)
from app.agent.planning.action_plan import (
    ActionPlan,
)

from app.agent.runtime.execution_context import (
    AgentExecutionContext,
)

from app.agent.perception.screen_scene import (
    ScreenScene,
)

from app.agent.reasoning.reasoning_task_planner import (
    ReasoningTaskPlanner,
)

from app.agent.reasoning.task_planning_context import (
    TaskPlanningContext,
)

from app.agent.reasoning.task_reasoner import (
    TaskReasoner,
)

from app.agent.skills.default_skills import (
    create_default_skill_registry,
)

from app.agent.skills.skill_registry import (
    SkillRegistry,
)


class AgentOrchestrator:
    """
    Coordinates the complete agent preparation flow.

    Flow:

        AgentRequest
             ↓
        AgentPlanner
             ↓
        Intent
             ↓
        CapabilityRouter
             ↓
        Capability
             ↓
        SkillRegistry
             ↓
        AgentSkill
             ↓
        AgentExecutionContext

    The orchestrator intentionally does not perform
    external actions.

    Its responsibility is to decide:

    - what the user wants
    - which capability should handle it
    - which specialized skill should handle it
    - whether human review is required

    Actual execution will be handled later by controlled
    executors and runtime adapters.
    """

    def __init__(
        self,
        planner: AgentPlanner | None = None,
        capability_router: CapabilityRouter | None = None,
        skill_registry: SkillRegistry | None = None,
        task_reasoner: TaskReasoner | None = None,
        application_knowledge: dict[str, object] | None = None,
        require_task_reasoning: bool = False,
    ) -> None:

        self.planner = (
            planner
            if planner is not None
            else AgentPlanner()
        )

        if capability_router is not None:
            self.capability_router = (
                capability_router
            )
        else:
            capability_registry = (
                create_default_capability_registry()
            )

            self.capability_router = (
                CapabilityRouter(
                    capability_registry
                )
            )

        self.skill_registry = (
            skill_registry
            if skill_registry is not None
            else create_default_skill_registry()
        )

        self.task_planner = (
            ReasoningTaskPlanner(task_reasoner)
            if task_reasoner is not None
            else None
        )

        self.application_knowledge = application_knowledge
        self.require_task_reasoning = require_task_reasoning

    def prepare(
        self,
        request: AgentRequest,
        initial_scene: ScreenScene | None = None,
        offer_workflow: dict[str, object] | None = None,
        application_knowledge: dict[str, object] | None = None,
        autonomous: bool = False,
    ) -> AgentExecutionContext:
        """
        Prepare one agent request for execution.

        This method:

        1. creates a semantic plan
        2. detects the intent
        3. resolves the required capability
        4. resolves the specialized skill
        5. returns a complete execution context

        No external actions are executed here.

        When an initial semantic scene is available, it is supplied to
        the task reasoner so planning can account for the current UI
        state before proposing an action.
        """

        deterministic_plan = self.planner.plan(
            request
        )

        intent = deterministic_plan.intent

        # Autonomous computer-use requests must not be blocked by the
        # deterministic intent keyword classifier. Unknown language is
        # precisely where model reasoning should take over after observation.
        if intent == AgentIntent.UNKNOWN and autonomous:
            intent = AgentIntent.COMPUTER_USE
            deterministic_plan = ActionPlan(
                intent=intent,
                steps=(),
                confidence=0.0,
                requires_manual_review=True,
            )

        if intent == AgentIntent.UNKNOWN:
            return AgentExecutionContext(
                request=request,
                intent=intent,
                plan=deterministic_plan,
                capability=None,
                skill=None,
                requires_manual_review=True,
            )

        capability = (
            self.capability_router.resolve(
                intent
            )
        )

        if capability is None:
            return AgentExecutionContext(
                request=request,
                intent=intent,
                plan=deterministic_plan,
                capability=None,
                skill=None,
                requires_manual_review=True,
            )

        skill = self.skill_registry.resolve(
            capability.name
        )

        if skill is None:
            return AgentExecutionContext(
                request=request,
                intent=intent,
                plan=deterministic_plan,
                capability=capability,
                skill=None,
                requires_manual_review=True,
            )

        if self.task_planner is not None:
            task_context = TaskPlanningContext(
                request_message=request.message,
                intent=intent.value,
                capability_name=capability.name,
                capability_description=(
                    capability.description
                ),
                skill_name=skill.__class__.__name__,
                scene=initial_scene,
                offer_workflow=offer_workflow,
                application_knowledge=(
                    application_knowledge
                    if application_knowledge is not None
                    else self.application_knowledge
                ),
            )

            reasoned_plan = self.task_planner.plan(
                context=task_context,
            )

            if reasoned_plan is not None:
                return AgentExecutionContext(
                    request=request,
                    intent=intent,
                    plan=reasoned_plan,
                    capability=capability,
                    skill=skill,
                    requires_manual_review=(
                        reasoned_plan.requires_manual_review
                    ),
                )

            if self.require_task_reasoning:
                failure_context = AgentExecutionContext(
                    request=request,
                    intent=intent,
                    plan=deterministic_plan,
                    capability=capability,
                    skill=skill,
                    requires_manual_review=True,
                )
                failure_context.set_value(
                    "task_reasoning_failure",
                    getattr(
                        self.task_planner,
                        "last_failure_reason",
                        "task_reasoner_failed",
                    ),
                )
                return failure_context

        skill_plan = skill.plan(
            request
        )

        return AgentExecutionContext(
            request=request,
            intent=intent,
            plan=skill_plan,
            capability=capability,
            skill=skill,
            requires_manual_review=(
                skill_plan.requires_manual_review
            ),
        )
