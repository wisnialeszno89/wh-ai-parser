"""One-process, observation-only NaviMind Windows control center.

The panel and WindowHub observer share the same NaviMindSharedHost instance.
This launcher never starts the V2 executor, sends model requests or performs
native inputs. To verify an offer after clicking Resume, bring WindowHub's
correct OFR document to foreground. UI remains responsive and human-first.

Windows: python tools/run_navimind_shared_control_center.py --expected-offer "OFR/1234-"
"""
from __future__ import annotations

import argparse
from queue import Empty, Full, Queue
from threading import Event, Thread
from pathlib import Path
import os
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.agent.runtime.navimind_panel_controller import PanelMode
from app.agent.runtime.navimind_shared_control_host import NaviMindSharedHost
from tools.run_navimind_control_panel import NaviMindPanel


def inspect_offer_in_background(*, observe, host, output: Queue, stop: Event,
                                wake_interval=0.4):
    """Only queues read-only observation; never calls Tk or grants permits."""
    while not stop.wait(wake_interval):
        if host.controller.snapshot().mode != PanelMode.RESUME_PENDING:
            continue
        observation_epoch = host.controller.arbiter.epoch
        try:
            observed = observe()
            item = ("scene", observation_epoch, observed)
        except Exception:
            item = ("error", observation_epoch, "read_only_observation_failed")
        if (host.controller.snapshot().mode != PanelMode.RESUME_PENDING
                or host.controller.arbiter.epoch != observation_epoch):
            continue
        try:
            output.put_nowait(item)
        except Full:
            # A slow UI must never block the observer or accumulate stale
            # screenshots. Next observation can replace this one.
            pass


def run(*, expected_offer: str) -> int:
    if os.name != "nt":
        print("NAVIMIND_SHARED_HOST_REQUIRES_WINDOWS=True")
        return 2
    host = NaviMindSharedHost(expected_offer)
    # Build the Windows UIA reader INSIDE its worker thread, not the Tk
    # thread. Native COM objects must remain in the apartment that owns them.
    queue: Queue = Queue(maxsize=2)
    stopped = Event()
    panel = NaviMindPanel(controller=host.controller)
    # Disclosure: connected host here means observation-only, never executor.
    panel.title("NaviMind • Workspace / WindowHub — OBSERWACJA")
    panel.host_observation_only = True
    panel._update(host.controller.snapshot())
    # The larger main window hosts chat + local PDF intake together.
    # Its control arbiter is shared with WindowHub observation.
    from app.agent.runtime.navimind_conversational_provider import ChatConfig, CompatibleChatProvider
    from app.agent.runtime.navimind_live_conversation import LiveMissionConversation
    try:
        config = ChatConfig.from_environment()
        chat_provider = CompatibleChatProvider(config) if config is not None else None
    except (ValueError, TypeError):
        chat_provider = None
    # Ground the model in THIS launcher's verified capabilities, not in
    # generic product aspirations or the untrusted customer prompt.
    runtime_instructions = (
        "NaviMind działa lokalnie na Windows. Program ma otwarty panel "
        "rozmowy i dostępny obserwator UIA, który może w trybie tylko-odczyt "
        "zweryfikować aktywny dokument WindowHub po kliknięciu Wznów pracę. "
        "Czytanie aktywnego dokumentu wymaga niezależnej obserwacji; nie "
        "twierdź, że aktualnie widzisz dowolne pola ani że znasz wybranego klienta. "
        "W tym procesie wykonawca V2 NIE jest podłączony; nie możesz "
        "teraz klikać w WindowHub, tworzyć okien, wpisywać parametrów, "
        "zapisywać ani wysyłać ofert. To ograniczenie aktualnego trybu "
        "uruchomienia, nie ogólna niemożliwość działania lokalnie. "
        "Możesz rozmawiać, analizować tekst wpisany bezpośrednio do czatu "
        "i przygotować konkretny plan dwóch pozycji. Dolne pole zapytania "
        "i PDF są lokalne i NIE SĄ wysyłane do modelu. "
        "Gdy użytkownik pyta o możliwość pracy lokalnej, wyjaśnij "
        "istniejący obserwator, brak wykonawcy V2 i następny krok "
        "integracyjny. Nie udawaj wykonania czynności."
    )
    live_chat = LiveMissionConversation(
        host.chat, chat_provider, runtime_instructions=runtime_instructions,
    )
    from app.agent.runtime.navimind_enquiry_inbox import LocalEnquiryInbox
    intake = LocalEnquiryInbox()
    panel.mount_main_workspace(
        chat=host.chat, conversation=live_chat, enquiry=intake,
    )
    print("NAVIMIND_MAIN_WORKSPACE_CONNECTED=True")
    print("NAVIMIND_ENQUIRY_LOCAL_ONLY=True")
    print("NAVIMIND_MICROPHONE_WINDOWS_DICTATION=True")

    def pump():
        while True:
            try:
                kind, observed_epoch, payload = queue.get_nowait()
            except Empty:
                break
            if (host.controller.snapshot().mode != PanelMode.RESUME_PENDING
                    or host.controller.arbiter.epoch != observed_epoch):
                continue
            if kind == "scene":
                try:
                    proof = host.inspect_fresh_scene(payload)
                    if proof.verified:
                        print("NAVIMIND_OFFER_VERIFIED_READ_ONLY=True")
                except (ValueError, RuntimeError):
                    host.last_reason = "read_only_verification_refused"
            else:
                host.last_reason = payload
        if not stopped.is_set():
            panel.after(250, pump)

    old_close = panel._close

    def close():
        stopped.set()
        host.takeover()
        live_chat.close()
        old_close()

    panel.protocol("WM_DELETE_WINDOW", close)
    def observer_worker():
        com_initialized = False
        try:
            try:
                import pythoncom
                pythoncom.CoInitialize()
                com_initialized = True
            except ImportError:
                pythoncom = None
            from app.agent.runtime.windows_desktop_agent_control_loop import (
                create_windows_desktop_agent_control_loop,
            )
            loop = create_windows_desktop_agent_control_loop()
            inspect_offer_in_background(
                observe=loop.observe_scene, host=host,
                output=queue, stop=stopped,
            )
        except Exception as exc:
            try:
                queue.put_nowait(("error", host.controller.arbiter.epoch,
                                  "observer_unavailable:" + type(exc).__name__))
            except Full:
                pass
        finally:
            if com_initialized:
                pythoncom.CoUninitialize()

    watcher = Thread(target=observer_worker, daemon=True)
    watcher.start()
    panel.after(250, pump)
    print("NAVIMIND_SHARED_PANEL_CONNECTED=True")
    print("NAVIMIND_CONVERSATION_PROVIDER_CONNECTED=" + str(chat_provider is not None))
    print("NAVIMIND_V2_EXECUTOR_CONNECTED=False")
    print("NAVIMIND_GUI_INPUT_EXECUTED=False")
    panel.mainloop()
    stopped.set()
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description="Read-only NaviMind shared Windows panel")
    parser.add_argument("--expected-offer", required=True,
                        help="Exact disposable OFR document caption, e.g. OFR/4687-")
    args = parser.parse_args(argv)
    return run(expected_offer=args.expected_offer)


if __name__ == "__main__":
    raise SystemExit(main())
