"""Offline NaviMind real-chat integration demonstration with fake model transport.

One human instruction arrives during the first model answer. The old
answer is discarded and only the newer mission revision receives a reply.
No internet, GUI actions, saving, or WindowHub process required.
"""
from __future__ import annotations

from pathlib import Path
from threading import Event
import time
import sys
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.agent.runtime.navimind_conversational_provider import (
    ChatConfig, CompatibleChatProvider,
)
from app.agent.runtime.navimind_live_conversation import LiveMissionConversation
from app.agent.runtime.navimind_shared_control_host import NaviMindSharedHost


def main() -> int:
    entered = Event()
    release = Event()
    calls = []

    def fake_http(config, body):
        import json
        transcript = json.loads(body)["messages"]
        calls.append(transcript)
        entered.set()
        release.wait(3)
        return {
            "choices": [{"message": {
                "content": "Rozumiem zmianę. Przygotuję pozycję opisową panelu EK-02-A, "
                           "cenę pozostawię nieustaloną. Nie zapisałem oferty."
            }}],
        }

    host = NaviMindSharedHost("OFR/101")
    provider = CompatibleChatProvider(
        ChatConfig("https://api.example.org/v1/chat/completions",
                   "offline-demo-model", "offline-demo-key"),
        transport=fake_http,
    )
    conversation = LiveMissionConversation(host.chat, provider)
    first = host.chat.user_message("Dodaj drzwi z panelem zewnętrznym")
    assert conversation.submit_current_message(first.message_id)
    assert entered.wait(2)
    newer = host.chat.user_message(
        "Dodaj panel EK-02-A i nie wpisuj żadnej nieznanej ceny"
    )
    assert conversation.submit_current_message(newer.message_id)
    release.set()
    deadline = time.monotonic() + 3
    while conversation.status().active and time.monotonic() < deadline:
        time.sleep(0.01)
    latest = host.chat.snapshot()
    replies = [m for m in latest.messages if m.role.value == "agent"]
    print("SYNTHETIC_MODEL_ONLY=True")
    print("HUMAN_MESSAGES=" + str(sum(m.role.value == "human" for m in latest.messages)))
    print("MODEL_CALLS=" + str(len(calls)))
    print("STALE_RESPONSE_DROPPED=" + str(len(replies) == 1))
    print("LATEST_REPLY_MISSION_REVISION=" + str(
        replies[0].mission_revision if replies else -1
    ))
    print("HUMAN_CONTROLS_DESKTOP=" + str(host.controller.snapshot().human_controls))
    print("AGENT_INPUT_PERMIT=" + str(host.controller.current_permit() is not None))
    print("REAL_CHAT_NETWORK_REQUESTS=0")
    print("WINDOWHUB_GUI_ACTIONS=0")
    conversation.close()
    return 0 if (
        len(calls) == 2 and len(replies) == 1
        and replies[0].mission_revision == 2
        and host.controller.snapshot().human_controls
        and host.controller.current_permit() is None
    ) else 1


if __name__ == "__main__":
    raise SystemExit(main())
