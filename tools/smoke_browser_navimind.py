from __future__ import annotations

import os
import sys
from pathlib import Path

# Allow direct execution via python tools/<script>.py from the repository root.
# Python otherwise puts tools/ rather than the repository root on sys.path.
REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from app.agent.agent_request import AgentRequest
from app.agent.runtime.browser_agent_runtime import (
    create_browser_agent_runtime,
)


def main() -> int:
    if os.getenv("AGENT_BROWSER_ENABLED", "0").strip() != "1":
        raise SystemExit(
            "AGENT_BROWSER_ENABLED=1 is required for this smoke test."
        )

    if os.getenv("AGENT_BROWSER_DRY_RUN", "1").strip() != "1":
        raise SystemExit(
            "Refusing to run: AGENT_BROWSER_DRY_RUN must be 1."
        )

    runtime = create_browser_agent_runtime()

    try:
        result = runtime.run(
            AgentRequest(
                message=(
                    "Otwórz stronę https://example.com "
                    "w przeglądarce."
                ),
                metadata={
                    "target_application": "Browser",
                },
            )
        )

        plan = result.context.plan
        action = (
            plan.steps[0].action
            if plan is not None and plan.steps
            else None
        )

        print("=" * 72)
        print("BROWSER -> NAVIMIND SMOKE")
        print("=" * 72)
        print("intent:", result.intent.value)
        print("runtime_executed:", result.executed)
        control = result.control_loop_result
        browser_action_executed = None
        if control is not None and control.last_execution_result is not None:
            attempt = control.last_execution_result.last_attempt
            if attempt is not None:
                execution_result = attempt.execution_result
                metadata = execution_result.metadata or {}
                browser_action_executed = metadata.get("executed")
        print("browser_action_executed:", browser_action_executed)
        print(
            "requires_manual_review:",
            result.requires_manual_review,
        )
        print(
            "reasoning_failure:",
            result.context.get_value(
                "task_reasoning_failure"
            ),
        )
        browser_page = result.context.get_value(
            "browser_page",
        )
        print(
            "browser_url:",
            getattr(browser_page, "url", None),
        )
        print(
            "browser_title:",
            getattr(browser_page, "title", None),
        )
        print(
            "planned_action:",
            action.name if action is not None else None,
        )
        print(
            "target:",
            action.target if action is not None else None,
        )
        print(
            "value:",
            action.value if action is not None else None,
        )
        print(
            "plan_confidence:",
            plan.confidence if plan is not None else None,
        )
        print("=" * 72)

        return 0

    finally:
        provider = getattr(
            runtime.browser_adapter,
            "_provider",
            None,
        )
        close = getattr(
            provider,
            "close",
            None,
        )
        if callable(close):
            close()


if __name__ == "__main__":
    raise SystemExit(main())
