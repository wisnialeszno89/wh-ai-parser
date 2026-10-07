from __future__ import annotations

import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread

# Allow direct execution via python tools/<script>.py from the repository root.
REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from app.agent.agent_request import AgentRequest
from app.agent.runtime.browser_agent_runtime import (
    create_browser_agent_runtime,
)

FIXTURE_HTML = (
    Path(__file__).resolve().parent
    / "fixtures"
    / "browser_multistep_form.html"
).read_text(encoding="utf-8")


class FixtureHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path != "/":
            self.send_error(404)
            return

        payload = FIXTURE_HTML.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, format, *args) -> None:
        return


def main() -> int:
    if os.getenv("AGENT_BROWSER_LIVE_CONFIRM", "0").strip() != "1":
        raise SystemExit(
            "Refusing live browser test: set AGENT_BROWSER_LIVE_CONFIRM=1 explicitly."
        )

    if not os.getenv("NAVIMIND_AGENT_URL", "").strip():
        raise SystemExit("NAVIMIND_AGENT_URL must be configured.")

    server = ThreadingHTTPServer(("127.0.0.1", 0), FixtureHandler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()

    fixture_url = f"http://127.0.0.1:{server.server_port}/"
    os.environ["AGENT_BROWSER_ENABLED"] = "1"
    os.environ["AGENT_BROWSER_DRY_RUN"] = "0"
    os.environ["AGENT_BROWSER_HEADLESS"] = "1"
    os.environ["AGENT_BROWSER_ALLOWED_DOMAINS"] = "127.0.0.1"

    runtime = create_browser_agent_runtime()

    try:
        result = runtime.run_autonomous(
            AgentRequest(
                message=(
                    f"Otwórz stronę {fixture_url}. Uzupełnij formularz zgodnie "
                    "z instrukcją na stronie: wpisz „Adam” w pole „Imię klienta”, "
                    "wybierz „Polska” w polu „Kraj”, następnie kliknij "
                    "„Zatwierdź formularz”. Zakończ dopiero, gdy strona pokaże "
                    "„Formularz zatwierdzony”. Wykonuj najwyżej jedną akcję "
                    "przeglądarki na cykl rozumowania."
                ),
                metadata={"target_application": "Browser"},
            ),
            max_steps=8,
        )

        print("=" * 72)
        print("BROWSER MULTISTEP FORM SMOKE")
        print("=" * 72)
        print("success:", result.success)
        print("completed:", result.completed)
        print("requires_manual_review:", result.requires_manual_review)
        print("stopped:", result.stopped)
        print("reason:", result.reason)
        print("cycles:", len(result.step_results))

        expected_actions = []
        physical_actions = []

        for index, step in enumerate(result.step_results, start=1):
            plan = step.context.plan
            action = (
                plan.steps[0].action
                if plan is not None and plan.steps
                else None
            )

            control = step.control_loop_result
            physical = None
            if (
                control is not None
                and control.last_execution_result is not None
                and control.last_execution_result.last_attempt is not None
            ):
                metadata = (
                    control.last_execution_result.last_attempt.execution_result.metadata
                    or {}
                )
                physical = metadata.get("executed")
                if "executed" in metadata:
                    physical_actions.append(physical)

            if action is not None:
                expected_actions.append(action.name)

            page = step.context.get_value("browser_page")

            print(f"--- cycle {index} ---")
            print("intent:", step.intent.value)
            print("runtime_executed:", step.executed)
            print("browser_action_executed:", physical)
            print("manual_review:", step.requires_manual_review)
            print("planned_action:", action.name if action else None)
            print("target:", action.target if action else None)
            print("value:", action.value if action else None)
            print(
                "plan_confidence:",
                plan.confidence if plan is not None else None,
            )
            print("browser_url:", getattr(page, "url", None))
            print("browser_title:", getattr(page, "title", None))
            print(
                "reasoning_failure:",
                step.context.get_value("task_reasoning_failure"),
            )

        print("=" * 72)

        if not result.success or not result.completed:
            return 1

        required = (
            "browser_navigate",
            "browser_write_text",
            "browser_select_option",
            "browser_click",
        )

        if not all(action in expected_actions for action in required):
            print("Missing one or more required semantic actions:", required)
            print("Observed actions:", expected_actions)
            return 2

        if sum(value is True for value in physical_actions) < 4:
            print("Expected four physical browser actions.")
            return 3

        return 0
    finally:
        provider = getattr(runtime.browser_adapter, "_provider", None)
        close = getattr(provider, "close", None)
        if callable(close):
            close()
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    raise SystemExit(main())
