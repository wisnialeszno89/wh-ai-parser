"""One bounded REAL AI Gateway request, with no UI or WindowHub dependency.

Invoked only by an explicit owner CLI flag. Never displays keys, payloads,
server response bodies, URL query strings or arbitrary exception details.
"""
from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.agent.runtime.navimind_conversational_provider import (
    ChatConfig, ChatUnavailable, CompatibleChatProvider,
)


def run_diagnostic(*, config=None, provider_factory=CompatibleChatProvider,
                   output=print) -> int:
    if config is None:
        try:
            config = ChatConfig.from_environment()
        except (ValueError, TypeError):
            output("NAVIMIND_GATEWAY_SMOKE=CONFIG_INVALID")
            return 2
    if config is None:
        output("NAVIMIND_GATEWAY_SMOKE=CONFIG_MISSING")
        return 2
    output("NAVIMIND_GATEWAY_SMOKE=REQUEST_STARTED")
    try:
        # Single tiny paid request only when the user explicitly starts this CLI.
        provider = provider_factory(config)
        answer = provider.reply(
            transcript=(("user", "Odpowiedz tylko: OK"),),
            instructions="Odpowiedz krótko po polsku jednym słowem: OK.",
        )
        if not answer.strip():
            raise ChatUnavailable("empty_chat_reply")
    except ChatUnavailable as exc:
        code = str(exc)
        # A future provider may throw malformed text: never emit it.
        safe_codes = {
            "chat_request_rejected_400", "chat_authentication_failed_401",
            "chat_gateway_credits_or_budget_402", "chat_gateway_access_denied_403",
            "chat_model_or_endpoint_not_found_404", "chat_gateway_timeout_408",
            "chat_request_validation_failed_422", "chat_gateway_rate_limited_429",
            "chat_provider_server_error_500", "chat_provider_gateway_error_502",
            "chat_provider_unavailable_503", "chat_provider_timeout_504",
            "chat_http_error_other", "chat_transport_unavailable",
            "chat_redirect_refused", "chat_response_not_ok",
            "chat_response_too_large", "invalid_chat_response",
            "empty_chat_reply", "chat_request_too_large", "chat_response_too_large",
        }
        output("NAVIMIND_GATEWAY_SMOKE=" + (code if code in safe_codes else "UNKNOWN_PROVIDER_ERROR"))
        return 1
    except Exception:
        output("NAVIMIND_GATEWAY_SMOKE=UNEXPECTED_ERROR")
        return 1
    output("NAVIMIND_GATEWAY_SMOKE=SUCCESS")
    output("NAVIMIND_GATEWAY_RESPONSE_NONEMPTY=True")
    output("NAVIMIND_WINDOWHUB_ACTIONS=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(run_diagnostic())
