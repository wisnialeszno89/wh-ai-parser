from __future__ import annotations

"""End-to-end probe for the Universal Agent Runtime + WindowHub.

This probe intentionally uses the WindowHub runtime factory, while the
configured robot executor remains DRY_RUN. It is therefore safe to use as
the first vertical-slice smoke test.

Run from the repository root:

    python tools/probe_universal_agent_runtime.py
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.agent.agent_request import AgentRequest
from app.agent.runtime.windowhub_agent_runtime import (
    create_windowhub_agent_runtime,
)


def _print_section(title: str) -> None:
    print()
    print("=" * 72)
    print(title)
    print("=" * 72)


def main() -> None:
    request = AgentRequest(
        message="Zrób wycenę okna 1230x1480 FIX",
    )

    _print_section("REQUEST")
    print(request.message)

    runtime = create_windowhub_agent_runtime()

    result = runtime.run(request)

    context = result.context
    plan = context.plan
    control = result.control_loop_result

    _print_section("INTENT")
    print(getattr(result.intent, "value", result.intent))

    _print_section("PLAN")
    if plan is None:
        print("No plan")
    else:
        print(f"confidence={plan.confidence}")
        print(f"requires_manual_review={plan.requires_manual_review}")
        for step in plan.steps:
            print(
                f"step[{step.index}] "
                f"action={step.action.name}"
            )

    if control is None:
        _print_section("CONTROL LOOP")
        print("Control loop was not configured or was not used.")
        print(f"executed={result.executed}")
        print(f"requires_manual_review={result.requires_manual_review}")
        return

    _print_section("OFFER CONTEXT")
    offer_context = context.get_value("offer_context")
    if offer_context is None:
        print("offer_context=None")
    else:
        print(f"product_type={offer_context.product_type}")
        print(f"width={offer_context.width}")
        print(f"height={offer_context.height}")
        print(f"quantity={offer_context.quantity}")
        print(f"opening={offer_context.opening}")
        print(f"openings={offer_context.openings}")
        print(f"missing_fields={offer_context.missing_fields}")
        print(f"conflicts={offer_context.conflicts}")

    _print_section("OBSERVATION / PERCEPTION")
    observation = getattr(context, "last_observation", None)
    print(f"observation_type={type(observation).__name__}")
    scene = getattr(context, "current_scene", None)
    print(f"scene_type={type(scene).__name__}")

    _print_section("DECISIONS")
    for i, decision in enumerate(control.decisions, start=1):
        print(
            f"decision[{i}] "
            f"type={getattr(decision.decision_type, 'value', decision.decision_type)} "
            f"reason={getattr(decision, 'reason', '')}"
        )

    _print_section("EXECUTION + VERIFICATION")
    for i, execution in enumerate(control.execution_results, start=1):
        print(
            f"execution[{i}] "
            f"success={execution.success} "
            f"requires_manual_review={execution.requires_manual_review}"
        )
        for attempt_index, attempt in enumerate(execution.attempts, start=1):
            execution_result = attempt.execution_result
            verification_result = attempt.verification_result
            print(
                f"  attempt[{attempt_index}] "
                f"execution_success={getattr(execution_result, 'success', None)} "
                f"verification_verified={getattr(verification_result, 'verified', None)}"
            )
            if execution_result is not None:
                print(
                    f"    execution_message="
                    f"{getattr(execution_result, 'message', '')}"
                )
            if verification_result is not None:
                print(
                    f"    verification_reason="
                    f"{getattr(verification_result, 'reason', '')}"
                )

    _print_section("STEP LIFECYCLE")
    for transition in control.step_transitions:
        print(
            f"{transition.action_name}: "
            f"{getattr(transition.from_status, 'value', transition.from_status)}"
            f" -> "
            f"{getattr(transition.to_status, 'value', transition.to_status)}"
        )

    _print_section("REPLAN")
    if not control.replan_records:
        print("No replanning performed.")
    for record in control.replan_records:
        print(
            f"{record.failed_action_name} -> "
            f"{', '.join(record.replacement_actions)} "
            f"(reason={record.reason}, attempts={record.attempts})"
        )

    _print_section("FINAL RESULT")
    print(
        f"success={control.success} "
        f"plan_status={getattr(control.plan_status, 'value', control.plan_status)} "
        f"stopped={control.stopped} "
        f"manual_review={control.requires_manual_review}"
    )
    print(f"executed_actions={control.executed_actions}")
    print(f"replanned_actions={control.replanned_actions}")
    print(f"failed_actions={control.failed_actions}")
    print(f"transitions={control.transition_count}")
    print(f"runtime_result.executed={result.executed}")
    print(
        "runtime_result.requires_manual_review="
        f"{result.requires_manual_review}"
    )


if __name__ == "__main__":
    main()
