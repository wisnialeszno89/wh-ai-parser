from dataclasses import dataclass

import pytest

from app.agent.adapters.browser_adapter import (
    BrowserAdapter,
    BrowserElement,
    BrowserPage,
)
from app.agent.agent_action import AgentAction
from app.agent.execution.browser_action_executor import (
    BrowserActionExecutor,
)
from app.agent.runtime.execution_context import ExecutionContext
from app.agent.agent_request import AgentRequest


@dataclass
class FakeBrowserProvider:
    available: bool = True

    def __post_init__(self):
        self.page = BrowserPage(
            url="https://example.com/start",
            title="Start",
            text="Hello",
            elements=(
                BrowserElement(
                    label="Dalej",
                    kind="button",
                    interaction_capability="CLICKABLE",
                    confidence=0.95,
                ),
                BrowserElement(
                    label="Imię",
                    kind="textbox",
                    interaction_capability="EDITABLE",
                    current_value="",
                    confidence=0.98,
                ),
                BrowserElement(
                    label="Profil",
                    kind="select",
                    interaction_capability="SELECTABLE",
                    current_value="",
                    confidence=0.97,
                ),
            ),
        )
        self.opened = []
        self.clicks = []
        self.writes = []
        self.selections = []
        self.back_count = 0

    def is_available(self):
        return self.available

    def open(self, url):
        self.opened.append(url)
        return self.page

    def current_page(self):
        return self.page

    def click(self, target):
        self.clicks.append(target.label)
        return self.page

    def write_text(self, target, value):
        self.writes.append((target.label, value))
        return self.page

    def select_option(self, target, value):
        self.selections.append((target.label, value))
        return self.page

    def back(self):
        self.back_count += 1
        return self.page


def create_context():
    return ExecutionContext(
        request=AgentRequest(
            message="browser test",
        )
    )


def create_executor(*, dry_run=False, available=True):
    provider = FakeBrowserProvider(
        available=available,
    )
    adapter = BrowserAdapter(
        provider=provider,
        allowed_domains=("example.com",),
        dry_run=dry_run,
    )
    return BrowserActionExecutor(adapter), adapter, provider


def test_browser_executor_supports_only_available_browser_actions():
    executor, _, _ = create_executor()

    supported = {
        "browser_navigate",
        "browser_read",
        "browser_click",
        "browser_write_text",
        "browser_select_option",
        "browser_back",
    }

    for name in supported:
        assert executor.supports(
            AgentAction(name=name, description="test")
        )

    assert not executor.supports(
        AgentAction(
            name="browser_delete",
            description="test",
        )
    )


def test_browser_executor_does_not_resolve_when_adapter_unavailable():
    executor, _, _ = create_executor(available=False)

    assert not executor.supports(
        AgentAction(
            name="browser_click",
            description="test",
        )
    )

    result = executor.execute(
        AgentAction(
            name="browser_click",
            description="test",
            target="Dalej",
        ),
        create_context(),
    )

    assert result.success is False
    assert result.requires_manual_review is True


def test_browser_executor_navigate_read_and_back():
    executor, _, provider = create_executor()
    context = create_context()

    navigate = executor.execute(
        AgentAction(
            name="browser_navigate",
            description="navigate",
            value="https://example.com/next",
        ),
        context,
    )
    read = executor.execute(
        AgentAction(
            name="browser_read",
            description="read",
        ),
        context,
    )
    back = executor.execute(
        AgentAction(
            name="browser_back",
            description="back",
        ),
        context,
    )

    assert navigate.success is True
    assert read.success is True
    assert back.success is True
    assert provider.opened == ["https://example.com/next"]
    assert provider.back_count == 1
    assert context.get_value("browser_page") == provider.page


def test_browser_executor_click_resolves_exact_semantic_target():
    executor, _, provider = create_executor()
    context = create_context()

    result = executor.execute(
        AgentAction(
            name="browser_click",
            description="click Dalej",
            target="dalej",
        ),
        context,
    )

    assert result.success is True
    assert provider.clicks == ["Dalej"]
    assert result.metadata == {
        "browser_operation": "click",
        "browser_url": "https://example.com/start",
        "browser_title": "Start",
        "executed": True,
        "target": "Dalej",
    }


def test_browser_executor_write_and_select_use_semantic_targets():
    executor, _, provider = create_executor()
    context = create_context()

    write_result = executor.execute(
        AgentAction(
            name="browser_write_text",
            description="write name",
            target="Imię",
            value="Adam",
        ),
        context,
    )
    select_result = executor.execute(
        AgentAction(
            name="browser_select_option",
            description="select profile",
            target="Profil",
            value="Veka Softline 82",
        ),
        context,
    )

    assert write_result.success is True
    assert select_result.success is True
    assert provider.writes == [("Imię", "Adam")]
    assert provider.selections == [
        ("Profil", "Veka Softline 82")
    ]


def test_browser_executor_fails_closed_for_missing_or_ambiguous_target():
    executor, _, provider = create_executor()
    context = create_context()

    missing = executor.execute(
        AgentAction(
            name="browser_click",
            description="missing",
            target="Nie ma",
        ),
        context,
    )

    assert missing.success is False
    assert provider.clicks == []

    provider.page = BrowserPage(
        url=provider.page.url,
        title=provider.page.title,
        text=provider.page.text,
        elements=(
            BrowserElement(
                label="Dalej",
                interaction_capability="CLICKABLE",
                confidence=0.95,
            ),
            BrowserElement(
                label="Dalej",
                interaction_capability="CLICKABLE",
                confidence=0.96,
            ),
        ),
    )

    context.set_value("browser_page", provider.page)

    ambiguous = executor.execute(
        AgentAction(
            name="browser_click",
            description="ambiguous",
            target="Dalej",
        ),
        context,
    )

    assert ambiguous.success is False
    assert provider.clicks == []


def test_browser_executor_rejects_technical_locator_targets():
    executor, _, provider = create_executor()
    context = create_context()

    for target in (
        "css=#submit",
        "xpath=//button[@id='submit']",
        "runtime_id=abc",
        "selector=.submit",
    ):
        result = executor.execute(
            AgentAction(
                name="browser_click",
                description="bad locator",
                target=target,
            ),
            context,
        )
        assert result.success is False

    assert provider.clicks == []


def test_browser_executor_validates_required_arguments():
    executor, _, provider = create_executor()
    context = create_context()

    cases = (
        AgentAction(
            name="browser_navigate",
            description="missing url",
        ),
        AgentAction(
            name="browser_write_text",
            description="missing value",
            target="Imię",
        ),
        AgentAction(
            name="browser_select_option",
            description="missing value",
            target="Profil",
        ),
        AgentAction(
            name="browser_click",
            description="missing target",
        ),
    )

    for action in cases:
        result = executor.execute(
            action,
            context,
        )
        assert result.success is False

    assert provider.opened == []
    assert provider.writes == []
    assert provider.selections == []
    assert provider.clicks == []


def test_browser_executor_dry_run_never_executes_provider_action():
    executor, adapter, provider = create_executor(
        dry_run=True,
    )
    context = create_context()

    result = executor.execute(
        AgentAction(
            name="browser_write_text",
            description="dry run",
            target="Imię",
            value="Adam",
        ),
        context,
    )

    assert result.success is True
    assert result.metadata["executed"] is False
    assert result.metadata["browser_operation"] == "write_text"
    assert provider.writes == []
    assert adapter.dry_run is True
