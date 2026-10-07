from dataclasses import dataclass

from app.agent.adapters.browser_adapter import (
    BrowserAdapter,
    BrowserElement,
    BrowserPage,
)
from app.agent.agent_action import AgentAction
from app.agent.execution.browser_action_executor import (
    BrowserActionExecutor,
)
from app.agent.execution.default_executors import (
    create_default_executor_registry,
)


@dataclass
class FakeBrowserProvider:
    available: bool = True

    def __post_init__(self):
        self.page = BrowserPage(
            url="https://example.com",
            title="Example",
            text="",
            elements=(
                BrowserElement(
                    label="Dalej",
                    kind="button",
                    interaction_capability="CLICKABLE",
                    confidence=0.95,
                ),
            ),
        )

    def is_available(self):
        return self.available

    def open(self, url):
        return self.page

    def current_page(self):
        return self.page

    def click(self, target):
        return self.page

    def write_text(self, target, value):
        return self.page

    def select_option(self, target, value):
        return self.page

    def back(self):
        return self.page


def test_default_registry_resolves_wh_executor():
    registry = (
        create_default_executor_registry()
    )

    action = AgentAction(
        name="build_construction",
        description="Build construction",
    )

    executor = registry.resolve(
        action
    )

    assert executor is not None
    assert executor.__class__.__name__ == (
        "WHActionExecutor"
    )


def test_default_registry_does_not_enable_browser_without_adapter():
    registry = create_default_executor_registry()

    action = AgentAction(
        name="browser_click",
        description="Click Dalej",
        target="Dalej",
    )

    assert registry.resolve(action) is None


def test_default_registry_registers_browser_executor_when_injected():
    provider = FakeBrowserProvider()
    adapter = BrowserAdapter(
        provider=provider,
        allowed_domains=("example.com",),
    )

    registry = create_default_executor_registry(
        browser_adapter=adapter,
    )

    action = AgentAction(
        name="browser_click",
        description="Click Dalej",
        target="Dalej",
    )

    executor = registry.resolve(action)

    assert isinstance(
        executor,
        BrowserActionExecutor,
    )
