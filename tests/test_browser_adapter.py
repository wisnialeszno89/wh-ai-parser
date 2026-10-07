from dataclasses import dataclass

import pytest

from app.agent.adapters.browser_adapter import (
    BrowserAdapter,
    BrowserElement,
    BrowserPage,
)


@dataclass
class FakeBrowserProvider:
    available: bool = True
    page: BrowserPage = BrowserPage(
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
        ),
    )

    def __post_init__(self):
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


def test_browser_adapter_descriptor_and_availability():
    provider = FakeBrowserProvider()
    adapter = BrowserAdapter(provider=provider)

    assert adapter.descriptor.adapter_id == "browser"
    assert "navigate" in adapter.descriptor.capabilities
    assert adapter.is_available()


def test_browser_adapter_allows_domain_and_https_navigation():
    provider = FakeBrowserProvider()
    adapter = BrowserAdapter(
        provider=provider,
        allowed_domains=("example.com",),
        dry_run=False,
    )

    page = adapter.open("https://app.example.com/login")

    assert page.url == "https://example.com/start"
    assert provider.opened == ["https://app.example.com/login"]


def test_browser_adapter_rejects_disallowed_or_unsafe_urls():
    adapter = BrowserAdapter(
        provider=FakeBrowserProvider(),
        allowed_domains=("example.com",),
        dry_run=False,
    )

    with pytest.raises(ValueError):
        adapter.open("file:///C:/secret.txt")

    with pytest.raises(PermissionError):
        adapter.open("https://evil.example.net")


def test_browser_adapter_dry_run_does_not_execute_provider_action():
    provider = FakeBrowserProvider()
    adapter = BrowserAdapter(
        provider=provider,
        dry_run=True,
    )

    target = provider.page.elements[0]
    adapter.click(target)
    adapter.write_text(provider.page.elements[1], "Adam")

    assert provider.clicks == []
    assert provider.writes == []


def test_browser_adapter_executes_semantic_actions_only_when_enabled():
    provider = FakeBrowserProvider()
    adapter = BrowserAdapter(
        provider=provider,
        dry_run=False,
    )

    clickable, editable = provider.page.elements
    adapter.click(clickable)
    adapter.write_text(editable, "Adam")
    adapter.back()

    assert provider.clicks == ["Dalej"]
    assert provider.writes == [("Imię", "Adam")]
    assert provider.back_count == 1


def test_browser_adapter_rejects_wrong_capability_and_invalid_confidence():
    adapter = BrowserAdapter(
        provider=FakeBrowserProvider(),
        dry_run=False,
    )

    editable = adapter._provider.current_page().elements[1]

    with pytest.raises(PermissionError):
        adapter.click(editable)

    unknown = BrowserElement(
        label="Niepewny",
        interaction_capability="CLICKABLE",
        confidence=-0.1,
    )

    with pytest.raises(ValueError):
        adapter.click(unknown)


def test_browser_page_and_elements_are_model_safe_payloads():
    provider = FakeBrowserProvider()
    page = provider.page

    payload = page.to_payload()

    assert payload["url"] == page.url
    assert payload["title"] == page.title
    assert payload["elements"][0]["label"] == "Dalej"
    assert "metadata" not in payload["elements"][0]


def test_browser_adapter_dry_run_still_validates_url_and_target():
    provider = FakeBrowserProvider()
    adapter = BrowserAdapter(
        provider=provider,
        allowed_domains=("example.com",),
        dry_run=True,
    )

    with pytest.raises(PermissionError):
        adapter.open("https://evil.example.net")

    unknown = BrowserElement(
        label="Niepewny",
        interaction_capability="UNKNOWN",
        confidence=0.9,
    )
    with pytest.raises(PermissionError):
        adapter.click(unknown)


def test_browser_adapter_rejects_zero_confidence_interaction():
    adapter = BrowserAdapter(
        provider=FakeBrowserProvider(),
        dry_run=False,
    )

    target = BrowserElement(
        label="Dalej",
        interaction_capability="CLICKABLE",
        confidence=0.0,
    )

    with pytest.raises(PermissionError):
        adapter.click(target)



def test_browser_adapter_rejects_disallowed_resulting_page():
    provider = FakeBrowserProvider(
        page=BrowserPage(
            url="https://evil.example.net/redirected",
            title="Unexpected",
            text="Blocked destination",
        )
    )
    adapter = BrowserAdapter(
        provider=provider,
        allowed_domains=("example.com",),
        dry_run=False,
    )

    with pytest.raises(PermissionError):
        adapter.open("https://example.com/start")
