"""AI conversation backend contracts; all transport and HTTP are synthetic."""
from __future__ import annotations

import json
import pytest

from app.agent.runtime.navimind_conversational_provider import (
    ChatConfig, ChatUnavailable, CompatibleChatProvider, SYSTEM_INSTRUCTIONS,
    transcript_for_chat,
)
from app.agent.runtime.navimind_local_input_arbiter import LocalInputArbiter
from app.agent.runtime.navimind_mission_chat import MissionChat


def configuration():
    return ChatConfig(
        "https://api.example.org/v1/chat/completions", "navimind-chat",
        "offline-secret",
    )


def test_real_chat_configuration_does_not_require_native_v2_action_endpoint():
    config = configuration()
    assert config.url.endswith("/v1/chat/completions")
    assert config.model == "navimind-chat"


@pytest.mark.parametrize("endpoint", [
    "http://api.example.org/v1/chat/completions",
    "https://api.example.org/execute",
    "file:///tmp/key",
    "https://user:password@api.example.org/v1/chat/completions",
    "https://api.example.org/v1/chat/completions?token=secret",
])
def test_untrusted_or_incompatible_endpoint_fails_closed(endpoint):
    with pytest.raises(ValueError):
        ChatConfig(endpoint, "model", "key")


def test_missing_environment_does_not_make_any_network_request(monkeypatch):
    for name in ("NAVIMIND_CHAT_URL", "NAVIMIND_CHAT_MODEL", "NAVIMIND_CHAT_API_KEY"):
        monkeypatch.delenv(name, raising=False)
    assert ChatConfig.from_environment() is None


def test_valid_model_response_is_text_not_an_action():
    captured = []

    def fake_transport(config, payload):
        request = json.loads(payload)
        captured.append(request)
        return {"choices": [{"message": {
            "role": "assistant",
            "content": "Przygotuję zmianę koloru do weryfikacji, bez zapisu."
        }}]}

    provider = CompatibleChatProvider(configuration(), transport=fake_transport)
    text = provider.reply(transcript=(("user", "Zmień kolor"),))
    assert "bez zapisu" in text
    assert captured[0]["messages"][0]["role"] == "system"
    assert captured[0]["messages"][1] == {
        "role": "user", "content": "Zmień kolor",
    }
    assert "tools" not in captured[0]
    assert "function_call" not in captured[0]


def test_model_cannot_supply_structured_native_action_payload():
    provider = CompatibleChatProvider(
        configuration(), transport=lambda c, p: {
            "choices": [{"message": {"content": {
                "action": "click", "target": "save_button"
            }}}],
        },
    )
    with pytest.raises(ChatUnavailable, match="empty_chat_reply"):
        provider.reply(transcript=(("user", "Zrób coś"),))


def test_invalid_llm_response_fails_closed():
    provider = CompatibleChatProvider(
        configuration(), transport=lambda c, p: {"choices": []},
    )
    with pytest.raises(ChatUnavailable, match="invalid_chat_response"):
        provider.reply(transcript=(("user", "Cześć"),))


def test_chat_transcript_uses_only_human_and_agent_messages():
    chat = MissionChat(document_key="OFR/101", arbiter=LocalInputArbiter())
    chat.user_message("Parapet cena nieznana")
    chat.agent_message("Nie wpisałem ceny.", based_on_revision=1)
    assert transcript_for_chat(chat.snapshot()) == (
        ("user", "Parapet cena nieznana"),
        ("assistant", "Nie wpisałem ceny."),
    )


def test_chat_model_does_not_get_document_key_without_user_disclosing_it():
    chat = MissionChat(document_key="OFR/PRIVATE123", arbiter=LocalInputArbiter())
    chat.user_message("Jak przygotować bramę bez ceny?")
    transcript = transcript_for_chat(chat.snapshot())
    assert "OFR/PRIVATE123" not in repr(transcript)


def test_long_answer_is_truncated_to_chat_safe_length():
    provider = CompatibleChatProvider(
        configuration(),
        transport=lambda c, p: {"choices": [
            {"message": {"content": "A" * 9000}},
        ]},
    )
    assert len(provider.reply(transcript=(("user", "Daj plan"),))) <= 3501


def test_configuration_refuses_missing_api_key():
    with pytest.raises(ValueError, match="chat_api_key_required"):
        ChatConfig("https://api.example.org/v1/chat/completions", "model", "")


def test_conversation_instructions_do_not_claim_execution():
    assert "Nie twierdź, że wykonałeś" in SYSTEM_INSTRUCTIONS
    assert "Nie przedstawiaj nieznanych cen" in SYSTEM_INSTRUCTIONS


@pytest.mark.parametrize("status,expected", [
    (401, "chat_authentication_failed_401"),
    (402, "chat_gateway_credits_or_budget_402"),
    (403, "chat_gateway_access_denied_403"),
    (404, "chat_model_or_endpoint_not_found_404"),
    (429, "chat_gateway_rate_limited_429"),
    (503, "chat_provider_unavailable_503"),
    (504, "chat_provider_timeout_504"),
    (599, "chat_http_error_other"),
])
def test_gateway_http_error_maps_to_safe_code_without_server_body(status, expected):
    from app.agent.runtime.navimind_conversational_provider import safe_gateway_http_error
    assert safe_gateway_http_error(status) == expected
    assert "secret" not in safe_gateway_http_error(status)


def test_http_response_does_not_echo_error_body(monkeypatch):
    from urllib.error import HTTPError
    from io import BytesIO
    from app.agent.runtime.navimind_conversational_provider import _http_chat
    import app.agent.runtime.navimind_conversational_provider as module

    class Opener:
        def open(self, request, timeout=None):
            raise HTTPError(
                request.full_url, 402, "secret-super-sensitive",
                {}, BytesIO(b"Bearer secret-super-sensitive"),
            )
    monkeypatch.setattr(module, "build_opener", lambda *args: Opener())
    with pytest.raises(ChatUnavailable, match="chat_gateway_credits_or_budget_402") as err:
        _http_chat(configuration(), b"{}")
    assert "secret-super-sensitive" not in str(err.value)
