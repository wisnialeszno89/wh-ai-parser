from __future__ import annotations

import os

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
        print("executed:", result.executed)
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
        print(
            "browser_url:",
            (
                result.context.browser_page.url
                if result.context.browser_page is not None
                else None
            ),
        )
        print(
            "browser_title:",
            (
                result.context.browser_page.title
                if result.context.browser_page is not None
                else None
            ),
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
