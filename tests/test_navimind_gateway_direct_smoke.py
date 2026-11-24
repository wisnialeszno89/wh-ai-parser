"""Offline tests for one-time, nonsecret diagnostic gateway request."""
from pathlib import Path

import pytest

from app.agent.runtime.navimind_conversational_provider import ChatConfig, ChatUnavailable
from tools.diagnose_navimind_gateway_chat import run_diagnostic


def config():
    return ChatConfig("https://ai-gateway.vercel.sh/v1/chat/completions",
                      "openai/gpt-4o-mini", "fake-offline-key")


def test_no_config_never_contacts_network(monkeypatch):
    import app.agent.runtime.navimind_conversational_provider as m
    for key in ("NAVIMIND_CHAT_URL", "NAVIMIND_CHAT_MODEL", "NAVIMIND_CHAT_API_KEY"):
        monkeypatch.delenv(key, raising=False)
    lines = []
    assert run_diagnostic(output=lines.append) == 2
    assert lines == ["NAVIMIND_GATEWAY_SMOKE=CONFIG_MISSING"]


def test_one_valid_answer_reports_success_without_printing_reply_or_key():
    calls = []
    class Provider:
        def __init__(self, supplied):
            self.config = supplied
        def reply(self, *, transcript, instructions):
            calls.append(transcript)
            return "OK, this reply contains a possible private string"
    lines = []
    assert run_diagnostic(config=config(), provider_factory=Provider, output=lines.append) == 0
    assert len(calls) == 1
    assert "NAVIMIND_GATEWAY_SMOKE=SUCCESS" in lines
    assert "NAVIMIND_WINDOWHUB_ACTIONS=0" in lines
    assert "private string" not in repr(lines)
    assert "fake-offline-key" not in repr(lines)


@pytest.mark.parametrize("code", [
    "chat_authentication_failed_401", "chat_gateway_credits_or_budget_402",
    "chat_gateway_access_denied_403", "chat_transport_unavailable",
])
def test_safe_provider_error_is_reported_without_body(code):
    class Provider:
        def __init__(self, config):
            pass
        def reply(self, *, transcript, instructions):
            raise ChatUnavailable(code)
    lines = []
    assert run_diagnostic(config=config(), provider_factory=Provider, output=lines.append) == 1
    assert lines[-1] == "NAVIMIND_GATEWAY_SMOKE=" + code


def test_unknown_provider_error_cannot_leak_raw_server_response():
    class Provider:
        def __init__(self, config):
            pass
        def reply(self, *, transcript, instructions):
            raise ChatUnavailable("SENSITIVE CREDENTIAL TOKEN")
    lines = []
    assert run_diagnostic(config=config(), provider_factory=Provider, output=lines.append) == 1
    assert lines[-1] == "NAVIMIND_GATEWAY_SMOKE=UNKNOWN_PROVIDER_ERROR"
    assert "SENSITIVE" not in repr(lines)


def test_launch_flag_does_not_need_live_windowhub_offer():
    code = (Path(__file__).resolve().parents[1] / "tools" /
            "start_navimind_owner.ps1").read_text(encoding="utf-8")
    assert "[switch]$DiagnoseChat" in code
    assert 'if ($DiagnoseChat)' in code
    assert 'python "tools/diagnose_navimind_gateway_chat.py"' in code
    assert '$env:COMPUTER_USE_LIVE = "0"' in code
