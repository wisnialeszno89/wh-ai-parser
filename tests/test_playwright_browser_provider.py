import pytest

from app.agent.execution.playwright_browser_provider import (
    PlaywrightBrowserProvider,
)


def test_playwright_provider_is_disabled_by_default(monkeypatch):
    monkeypatch.delenv("AGENT_BROWSER_ENABLED", raising=False)
    provider = PlaywrightBrowserProvider()
    assert provider.is_available() is False


def test_playwright_provider_requires_explicit_enable(monkeypatch):
    monkeypatch.setenv("AGENT_BROWSER_ENABLED", "0")
    provider = PlaywrightBrowserProvider()
    assert provider.is_available() is False


def test_playwright_provider_rejects_unknown_browser_type():
    with pytest.raises(ValueError):
        PlaywrightBrowserProvider(
            browser_type="internet-explorer"
        )


def test_playwright_provider_rejects_invalid_limits():
    with pytest.raises(ValueError):
        PlaywrightBrowserProvider(
            navigation_timeout_ms=0
        )

    with pytest.raises(ValueError):
        PlaywrightBrowserProvider(
            max_elements=0
        )


def test_playwright_provider_headless_env_is_configurable(monkeypatch):
    monkeypatch.setenv("AGENT_BROWSER_HEADLESS", "0")
    provider = PlaywrightBrowserProvider()
    assert provider.headless is False


def test_playwright_provider_closes_cleanly_without_starting_runtime():
    provider = PlaywrightBrowserProvider()
    provider.close()

    assert provider._playwright is None
    assert provider._browser is None
    assert provider._context is None
    assert provider._page is None


@pytest.mark.parametrize(
    ("value", "expected"),
    (
        ("1", True),
        ("true", True),
        ("YES", True),
        ("on", True),
        ("0", False),
        ("false", False),
        ("off", False),
    ),
)
def test_browser_env_bool(monkeypatch, value, expected):
    monkeypatch.setenv("TEST_BROWSER_BOOL", value)

    assert (
        PlaywrightBrowserProvider._env_bool(
            "TEST_BROWSER_BOOL",
            not expected,
        )
        == expected
    )


def test_element_details_script_normalizes_whitespace_without_corrupting_labels():
    script = PlaywrightBrowserProvider._ELEMENT_DETAILS_SCRIPT

    assert 'value.replace(/\\s+/g, " ").trim()' in script
    assert 'value.replace(/s+/g, " ").trim()' not in script
