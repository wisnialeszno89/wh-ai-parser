from __future__ import annotations

import os

from app.agent.adapters.browser_adapter import BrowserAdapter
from app.agent.adapters.default_adapters import (
    create_default_adapter_registry,
)
from app.agent.execution.playwright_browser_provider import (
    PlaywrightBrowserProvider,
)
from app.agent.reasoning.navimind_task_reasoner import (
    NaviMindTaskReasoner,
)
from app.agent.runtime.agent_runtime import AgentRuntime
from app.agent.runtime.browser_agent_control_loop import (
    create_browser_agent_control_loop,
)
from app.agent.runtime.agent_orchestrator import AgentOrchestrator


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)

    if value is None:
        return default

    return value.strip().casefold() in {
        "1",
        "true",
        "yes",
        "on",
    }


def _allowed_domains() -> tuple[str, ...]:
    value = os.getenv(
        "AGENT_BROWSER_ALLOWED_DOMAINS",
        "",
    )

    domains = tuple(
        item.strip()
        for item in value.split(",")
        if item.strip()
    )

    if not domains:
        raise RuntimeError(
            "AGENT_BROWSER_ALLOWED_DOMAINS must contain at least one domain."
        )

    return domains


def create_browser_agent_runtime() -> AgentRuntime:
    """
    Create the universal AgentRuntime in explicit Browser mode.

    Browser mode requires:
    - AGENT_BROWSER_ENABLED=1
    - NAVIMIND_AGENT_URL
    - AGENT_BROWSER_ALLOWED_DOMAINS
    """

    provider = PlaywrightBrowserProvider(
        browser_type=os.getenv(
            "AGENT_BROWSER_TYPE",
            "chromium",
        ),
        headless=_env_bool(
            "AGENT_BROWSER_HEADLESS",
            True,
        ),
        user_data_dir=os.getenv(
            "AGENT_BROWSER_USER_DATA_DIR"
        ) or None,
    )

    browser_adapter = BrowserAdapter(
        provider=provider,
        allowed_domains=_allowed_domains(),
        dry_run=_env_bool(
            "AGENT_BROWSER_DRY_RUN",
            True,
        ),
    )

    orchestrator = AgentOrchestrator(
        task_reasoner=NaviMindTaskReasoner(),
        require_task_reasoning=True,
        adapter_registry=create_default_adapter_registry(
            browser_provider=provider,
            browser_allowed_domains=browser_adapter.allowed_domains,
            browser_dry_run=browser_adapter.dry_run,
        ),
    )

    return AgentRuntime(
        orchestrator=orchestrator,
        control_loop=create_browser_agent_control_loop(
            browser_adapter=browser_adapter,
        ),
        browser_adapter=browser_adapter,
        browser_context_enabled=True,
    )
