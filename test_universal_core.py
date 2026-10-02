from app.agent.agent_action import AgentAction
from app.agent.agent_intent import AgentIntent
from app.agent.agent_request import AgentRequest
from app.agent.planning.action_plan import ActionPlan
from app.agent.planning.action_step import ActionStep
from app.agent.runtime.execution_context import ExecutionContext
from app.agent.runtime.windowhub_agent_control_loop import (
    create_windowhub_agent_control_loop,
)


def main() -> None:
    request = AgentRequest(
        message="Observe the current WindowHub environment.",
        session_id="universal-core-test",
    )

    action = AgentAction(
        name="observe_windowhub",
        description="Observe the current WindowHub environment.",
    )

    step = ActionStep(
        index=0,
        action=action,
    )

    plan = ActionPlan(
        intent=AgentIntent.OBSERVE_WORKFLOW,
        steps=(step,),
        confidence=1.0,
    )

    context = ExecutionContext(
        request=request,
    )

    control_loop = create_windowhub_agent_control_loop()

    print("=== UNIVERSAL AGENT CORE TEST ===")
    print(f"REQUEST: {request.message}")
    print(f"INTENT: {plan.intent}")
    print(f"ACTION: {action.name}")
    print(f"DESCRIPTION: {action.description}")
    print()

    result = control_loop.run(
        plan=plan,
        context=context,
    )

    print("=== RESULT ===")
    print(f"SUCCESS: {result.success}")
    print(f"PLAN STATUS: {result.plan_status}")
    print(f"STOPPED: {result.stopped}")
    print(
        f"MANUAL REVIEW: "
        f"{result.requires_manual_review}"
    )

    print()
    print("=== DECISIONS ===")

    for decision in result.decisions:
        print(
            f"- TYPE: {decision.decision_type}"
        )
        print(
            f"  REASON: {decision.reason}"
        )
        print(
            f"  TARGET: {decision.target}"
        )

    print()
    print("=== EXECUTION RESULTS ===")

    for execution_result in result.execution_results:
        print(execution_result)

    print()
    print("=== SCENE ===")

    scene = context.current_scene

    if scene is None:
        print("NO SCENE")
        return

    print(
        f"ELEMENT COUNT: "
        f"{len(scene.elements)}"
    )

    for index, element in enumerate(
        scene.elements,
        start=1,
    ):
        print(
            f"[{index}] "
            f"kind={element.kind} "
            f"label={element.label} "
            f"confidence={element.confidence} "
            f"bounds=("
            f"{element.x},"
            f"{element.y},"
            f"{element.width},"
            f"{element.height}"
            ")"
        )

        print(
            f"     metadata={element.metadata}"
        )


if __name__ == "__main__":
    main()
