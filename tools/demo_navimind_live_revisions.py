"""Codespaces demonstration: a message interrupts the existing shared mission.

All values synthetic; zero native GUI actions, model calls or installer usage.
"""
from __future__ import annotations

from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.agent.runtime.navimind_shared_control_host import NaviMindSharedHost
from app.agent.offers.navimind_quote_revision_planner import (
    QuoteChange, plan_quote_revision,
)
from app.agent.runtime.navimind_program_router import (
    InstalledProgram, ProgramRequirement, route_program,
)


def main() -> int:
    host = NaviMindSharedHost("OFR/101")
    message = host.chat.user_message("Zmień kolor poz. 2 i zaktualizuj cenę")
    print("CHAT_MESSAGE_ACCEPTED=" + str(message.message_id == 1))
    print("CHAT_MISSION_REVISION=" + str(host.chat.snapshot().mission_revision))
    print("CHAT_REPLAN_REQUIRED=" + str(host.chat.snapshot().requires_replan))
    print("HUMAN_CONTROL=" + str(host.controller.snapshot().human_controls))
    print("OLD_INPUT_PERMIT_AVAILABLE=" + str(host.controller.current_permit() is not None))

    changes = (
        QuoteChange("2", "colour", "white", "anthracite", 3, 2, True, True),
        QuoteChange("2", "price", "2800", "2950", 2, 2, True, True),
    )
    revision = plan_quote_revision(
        document_key="OFR/101", changes=changes,
        exact_document_verified=True, readback_fresh=True,
        rebuild_possible=True, rebuild_base_steps=12,
    )
    print("QUOTE_CHANGE_ROUTE=" + revision.route.value)
    print("ORIGINAL_DOCUMENT_PRESERVED=" + str(revision.original_document_preserved))
    program = route_program(
        ProgramRequirement("edit_quote", requires_editable_output=True),
        (InstalledProgram("windowhub", "WindowHub", ("edit_quote",),
                          True, True, supports_safe_edit=True),),
    )
    print("PROGRAM_ROUTE=" + program.route.value)
    print("PROGRAM_LAUNCHED=" + str(program.app_launched))
    print("REAL_AI_REPLY_CONNECTED=False")
    print("GUI_ACTIONS_EXECUTED=False")
    return 0 if (
        host.controller.snapshot().human_controls
        and revision.original_document_preserved
        and not program.app_launched
    ) else 1


if __name__ == "__main__":
    raise SystemExit(main())
