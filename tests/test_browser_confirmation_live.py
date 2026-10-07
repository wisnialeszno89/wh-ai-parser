from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from app.agent.adapters.browser_adapter import BrowserAdapter
from app.agent.agent_request import AgentRequest
from app.agent.execution.playwright_browser_provider import (
    PlaywrightBrowserProvider,
)
from app.agent.reasoning.reasoning_action import ReasoningAction
from app.agent.reasoning.reasoning_proposal import ReasoningProposal
from app.agent.reasoning.task_reasoner import TaskReasoner
from app.agent.runtime.agent_orchestrator import AgentOrchestrator
from app.agent.runtime.agent_runtime import AgentRuntime
from app.agent.runtime.browser_agent_control_loop import (
    create_browser_agent_control_loop,
)

FIXTURE_HTML = (
    Path(__file__).resolve().parent
    / "fixtures"
    / "browser_confirmation_fixture.html"
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


class RecordingPlaywrightBrowserProvider(PlaywrightBrowserProvider):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.click_calls = 0

    def click(self, target):
        self.click_calls += 1
        return super().click(target)


@dataclass
class ConfirmationReasoner(TaskReasoner):
    fixture_url: str

    def __post_init__(self):
        self.calls = 0

    def reason(self, context):
        self.calls += 1

        if self.calls == 1:
            return ReasoningProposal(
                actions=(
                    ReasoningAction(
                        name="browser_navigate",
                        description="Open the local confirmation fixture.",
                        value=self.fixture_url,
                    ),
                ),
                rationale="The requested confirmation control is on the fixture page.",
                confidence=0.99,
            )

        return ReasoningProposal(
            actions=(
                ReasoningAction(
                    name="browser_click",
                    description="Submit the order after explicit user confirmation.",
                    target="Zatwierdź zamówienie",
                    requires_confirmation=True,
                ),
            ),
            rationale="Submitting the order is a confirmation-bound action.",
            confidence=0.99,
        )


def test_real_playwright_confirmation_boundary_blocks_physical_click(monkeypatch):
    if os.getenv("AGENT_BROWSER_LIVE_CONFIRM", "0").strip() != "1":
        pytest.skip(
            "Set AGENT_BROWSER_LIVE_CONFIRM=1 to run the real Playwright confirmation smoke."
        )

    monkeypatch.setenv("AGENT_BROWSER_ENABLED", "1")
    monkeypatch.setenv("AGENT_BROWSER_DRY_RUN", "0")
    monkeypatch.setenv("AGENT_BROWSER_HEADLESS", "1")
    monkeypatch.setenv("AGENT_BROWSER_ALLOWED_DOMAINS", "127.0.0.1")

    server = ThreadingHTTPServer(("127.0.0.1", 0), FixtureHandler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()

    fixture_url = f"http://127.0.0.1:{server.server_port}/"
    provider = RecordingPlaywrightBrowserProvider(
        browser_type="chromium",
        headless=True,
    )
    adapter = BrowserAdapter(
        provider=provider,
        allowed_domains=("127.0.0.1",),
        dry_run=False,
    )
    runtime = AgentRuntime(
        orchestrator=AgentOrchestrator(
            task_reasoner=ConfirmationReasoner(
                fixture_url=fixture_url,
            ),
            require_task_reasoning=True,
        ),
        control_loop=create_browser_agent_control_loop(
            browser_adapter=adapter,
        ),
        browser_adapter=adapter,
        browser_context_enabled=True,
    )

    try:
        result = runtime.run_autonomous(
            AgentRequest(
                message="Otwórz stronę testową i zatwierdź zamówienie.",
                metadata={"target_application": "Browser"},
            ),
            max_steps=5,
        )

        assert result.success is False
        assert result.completed is False
        assert result.requires_manual_review is True
        assert result.stopped is True
        assert result.reason == "control_loop_requires_manual_review"

        assert len(result.step_results) == 2
        assert result.step_results[0].control_loop_result is not None
        assert (
            result.step_results[0].control_loop_result.executed_actions
            == 1
        )

        second = result.step_results[1]
        assert second.requires_manual_review is True
        assert second.control_loop_result is not None
        assert second.control_loop_result.executed_actions == 0
        assert second.control_loop_result.requires_manual_review is True

        assert provider.click_calls == 0

        page = provider.current_page()
        assert page.title == "Browser Confirmation Fixture"
        assert "Oczekuje na potwierdzenie." in page.text
        assert any(
            element.label == "Zatwierdź zamówienie"
            for element in page.elements
        )
    finally:
        provider.close()
        server.shutdown()
        server.server_close()
