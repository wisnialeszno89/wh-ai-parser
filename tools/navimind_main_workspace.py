"""Integrated NaviMind workspace: chat, enquiry/PDF intake and Windows dictation.

Every submission goes to the same MissionChat / LiveMissionConversation as
the verified WindowHub host. No uploaded document is sent anywhere merely by
being attached. Native control remains observation-only in the current host.
"""
from __future__ import annotations

import ctypes
import re
import unicodedata
from queue import Empty, Queue
from threading import Thread
import os
import tkinter as tk
from tkinter import filedialog, messagebox

from app.agent.runtime.navimind_enquiry_inbox import EnquiryInputError, LocalEnquiryInbox
from app.agent.runtime.navimind_mission_chat import MessageRole, MissionChat


def _normalized_request(text: str) -> str:
    """Normalize colloquial Polish without executing instructions in prose."""
    folded = unicodedata.normalize("NFKD", text.casefold())
    plain = "".join(char for char in folded if not unicodedata.combining(char))
    return re.sub(r"[^a-z0-9]+", " ", plain).strip()


def requested_local_tool(text: str) -> str | None:
    """Conservative first local tool intent; all other prompts remain LLM chat."""
    words = set(_normalized_request(text).split())
    target = (
        "windowhub" in words or "wh" in words
        or ("program" in words and "okna" in words)
        or ("aplikacje" in words and "okna" in words)
    )
    if not target:
        return None
    if words.intersection({"otworz", "uruchom", "wlacz", "zainstaluj",
                           "usun", "zamknij", "kliknij", "wpisz",
                           "zrob", "utworz", "stworz", "zapisz"}):
        return None
    return ("discover_windowhub" if words.intersection({
        "znajdz", "wyszukaj", "odszukaj", "zlokalizuj", "sprawdz",
        "szukaj", "wykryj", "czy", "gdzie",
    }) else None)


def windowhub_discovery_answer(lines: tuple[str, ...]) -> str:
    """Only grounded, non-sensitive findings from trusted local tool."""
    if "WINDOWHUB_DISCOVERY=FOUND" in lines:
        location = ("na pierwszym planie"
                    if "WINDOWHUB_IS_FOREGROUND=True" in lines else "w tle")
        if "WINDOWHUB_ALL_MINIMIZED=True" in lines:
            location = "w zminimalizowanym oknie"
        return (
            "Znalazłem uruchomiony WindowHub (Okna.exe) " + location + ". "
            "Potwierdziłem obecność programu lokalnie, bez przejmowania myszy. "
            "To nie oznacza jeszcze odczytu bieżącej oferty ani możliwości "
            "tworzenia lub zapisywania konstrukcji."
        )
    if "WINDOWHUB_DISCOVERY=NOT_FOUND" in lines:
        return (
            "Nie znalazłem widocznego okna WindowHub w bieżącej sesji Windows. "
            "Uruchom program i napisz „sprawdź WH ponownie”. "
            "Nie twierdzę, że nie jest zainstalowany — sprawdziłem tylko "
            "uruchomione widoczne okna."
        )
    return ("Nie udało mi się odczytać listy okien Windows. "
            "Nie uruchamiałem ani nie modyfikowałem żadnej aplikacji.")


def chat_intake_decision(text: str, *, max_chars: int = MissionChat.MAX_MESSAGE_CHARS) -> str:
    """Choose a safe UI flow before handing free text to MissionChat."""
    if not isinstance(text, str) or not text.strip():
        return "empty"
    if len(text.strip()) > max_chars:
        return "long_enquiry"
    return "chat"

from app.agent.runtime.navimind_live_conversation import LiveMissionConversation
from tools.run_navimind_control_panel import BG, CARD, FG, MUTED, PURPLE, GOLD, STROKE


GATEWAY_ERROR_LABELS = {
    "chat_authentication_failed_401": "Błąd AI 401: klucz Vercel Gateway nie został zaakceptowany.",
    "chat_gateway_credits_or_budget_402": "Błąd AI 402: brak środków albo przekroczony budżet Gateway.",
    "chat_gateway_access_denied_403": "Błąd AI 403: Vercel odmawia dostępu; sprawdź weryfikację konta.",
    "chat_model_or_endpoint_not_found_404": "Błąd AI 404: model lub adres API jest niedostępny.",
    "chat_gateway_rate_limited_429": "Błąd AI 429: limit żądań; spróbuj później.",
    "chat_transport_unavailable": "Błąd połączenia AI: sieć, TLS lub przekroczony czas odpowiedzi.",
    "chat_provider_unavailable_503": "Błąd AI 503: usługa modelu chwilowo niedostępna.",
    "chat_provider_timeout_504": "Błąd AI 504: serwer modelu nie odpowiedział.",
    "chat_model_unavailable_or_invalid_response": "Model nie zwrócił poprawnej odpowiedzi.",
    "chat_unexpected_response_error": "Nieoczekiwany błąd odpowiedzi modelu.",
}


def friendly_chat_error(code: str | None) -> str:
    """Show a useful, bounded diagnostic, never raw remote error content."""
    if not code:
        return ""
    return GATEWAY_ERROR_LABELS.get(code, "Błąd modelu AI: " + code
                                    if code.startswith("chat_") and len(code) < 70
                                    else "Błąd modelu AI — sprawdź konfigurację.")


def chat_view_near_bottom(last_fraction: float, *, tolerance: float = 0.03) -> bool:
    """Follow incoming messages only when the operator is already near bottom."""
    return float(last_fraction) >= 1.0 - tolerance


def scroll_history_lines(delta: int) -> int:
    """Translate one Windows mouse wheel delta into Tk Text yview units."""
    if delta == 0:
        return 0
    return -max(1, abs(delta) // 120) if delta > 0 else max(1, abs(delta) // 120)


def windows_dictation_available() -> bool:
    """Windows' own Win+H dictation, not a custom or background audio listener."""
    return os.name == "nt"


def start_windows_dictation(widget, *, hotkey=None) -> bool:
    """Explicit click activates Windows dictation for the focused chat entry.

    No automatic recording, microphone permission escalation, or captured
    audio goes through NaviMind. The user reviews/edit text before sending.
    Windows online speech processing and permissions follow system settings.
    """
    if not windows_dictation_available():
        return False
    widget.focus_set()
    if hotkey is not None:
        hotkey()
        return True
    # Keybd_event is used only after the user clicks the microphone button.
    # Press+release Win+H. No WindowHub control or arbitrary shortcuts.
    user32 = ctypes.windll.user32
    VK_LWIN, VK_H, KEYEVENTF_KEYUP = 0x5B, 0x48, 0x0002
    user32.keybd_event(VK_LWIN, 0, 0, 0)
    user32.keybd_event(VK_H, 0, 0, 0)
    user32.keybd_event(VK_H, 0, KEYEVENTF_KEYUP, 0)
    user32.keybd_event(VK_LWIN, 0, KEYEVENTF_KEYUP, 0)
    return True


class NaviMindMainWorkspace(tk.Frame):
    """Embedded directly in the main NaviMind control window."""

    def __init__(self, parent, *, chat: MissionChat,
                 conversation: LiveMissionConversation | None,
                 enquiry: LocalEnquiryInbox | None = None,
                 discover_windowhub=None):
        super().__init__(parent, bg=BG)
        self.chat = chat
        self.conversation = conversation
        self.enquiry = enquiry or LocalEnquiryInbox()
        self.last_id = 0
        self.discover_windowhub = discover_windowhub
        self._discovery_queue = Queue(maxsize=1)
        self._discovery_active = False
        self._build()
        self._poll()

    def _label(self, parent, value, *, size=10, color=FG, bold=False):
        return tk.Label(
            parent, text=value, bg=parent.cget("bg"), fg=color,
            font=("Segoe UI Semibold" if bold else "Segoe UI", size),
            anchor="w",
        )

    def _build(self):
        tk.Label(
            self, text="NaviMind • Workspace", bg=BG, fg=FG,
            font=("Segoe UI Semibold", 17), anchor="w",
        ).pack(fill="x", padx=18, pady=(15, 2))
        self._label(
            self, "Rozmowa i dokumenty klienta w jednym miejscu • bez automatycznej edycji WindowHub",
            size=9, color=MUTED,
        ).pack(fill="x", padx=18, pady=(0, 10))

        top = tk.Frame(self, bg=CARD)
        top.pack(fill="both", expand=True, padx=18, pady=(0, 10))
        chat_heading = tk.Frame(top, bg=CARD)
        chat_heading.pack(fill="x", padx=12, pady=(9, 0))
        self._label(chat_heading, "ROZMOWA Z AGENTEM", size=9, color=GOLD, bold=True).pack(side="left")
        active = self.conversation is not None and self.conversation.status().provider_connected
        self.provider_indicator = self._label(
            chat_heading,
            "MODEL AI: PODŁĄCZONY" if active else "MODEL AI: NIEPODŁĄCZONY",
            size=9, color="#93D9BE" if active else GOLD,
        )
        self.provider_indicator.pack(side="right")
        history_box = tk.Frame(top, bg=CARD)
        history_box.pack(fill="both", expand=True, padx=(5, 10), pady=4)
        self.history_scrollbar = tk.Scrollbar(
            history_box, orient="vertical", width=13, takefocus=True,
        )
        self.history_scrollbar.pack(side="right", fill="y")
        self.history = tk.Text(
            history_box, wrap="word", bg=CARD, fg=FG, insertbackground=FG,
            relief="flat", font=("Segoe UI", 10), state="disabled",
            padx=12, pady=8, height=8,
            yscrollcommand=self.history_scrollbar.set,
            takefocus=True,
        )
        self.history.pack(side="left", fill="both", expand=True)
        self.history_scrollbar.configure(command=self.history.yview)
        self.history.bind("<MouseWheel>", self._history_mousewheel)
        self.history.bind("<Button-4>", self._history_mousewheel_linux)
        self.history.bind("<Button-5>", self._history_mousewheel_linux)
        self.history.bind("<Control-End>", self._history_bottom_shortcut)
        self.history.bind("<Control-Home>", self._history_top_shortcut)

        history_actions = tk.Frame(top, bg=CARD)
        history_actions.pack(fill="x", padx=12, pady=(0, 8))
        self._label(
            history_actions, "Przewijaj historię kółkiem myszy lub paskiem po prawej.",
            size=8, color=MUTED,
        ).pack(side="left")
        tk.Button(
            history_actions, text="↓ Najnowsze", command=self._history_to_bottom,
            fg=FG, bg="#29253A", relief="flat", padx=10, pady=3,
        ).pack(side="right")

        self._label(
            self, "Napisz lub podyktuj polecenie (Ctrl+Enter — wyślij)",
            size=9, color=MUTED,
        ).pack(fill="x", padx=18)
        self.entry = tk.Text(
            self, wrap="word", bg="#252535", fg=FG, height=3,
            insertbackground=FG, font=("Segoe UI", 10), relief="flat",
            padx=10, pady=7,
        )
        self.entry.pack(fill="x", padx=18, pady=(5, 7))
        self.entry.bind("<Control-Return>", self._keyboard_send)

        buttons = tk.Frame(self, bg=BG)
        buttons.pack(fill="x", padx=18, pady=(0, 8))
        self.mic = tk.Button(
            buttons, text="🎙 Dyktuj (Win+H)", command=self._dictate,
            fg=FG, bg="#29253A", relief="flat",
            font=("Segoe UI Semibold", 10), padx=10, pady=7,
        )
        self.mic.pack(side="left")
        if not windows_dictation_available():
            self.mic.configure(state="disabled")
        tk.Button(
            buttons, text="Wyślij", command=self._send,
            fg="#151020", bg=PURPLE, relief="flat",
            font=("Segoe UI Semibold", 10), padx=18, pady=7,
        ).pack(side="right")

        tk.Frame(self, height=1, bg=STROKE).pack(fill="x", padx=18, pady=(2, 7))
        heading = tk.Frame(self, bg=BG)
        heading.pack(fill="x", padx=18)
        self._label(
            heading, "ZAPYTANIE KLIENTA / PDF", size=9, color=GOLD, bold=True,
        ).pack(side="left")
        self.source_status = self._label(heading, "Brak dokumentów", size=9, color=MUTED)
        self.source_status.pack(side="right")
        self.enquiry_editor = tk.Text(
            self, height=5, wrap="word", bg=CARD, fg=FG, insertbackground=FG,
            relief="flat", font=("Segoe UI", 10), padx=10, pady=8,
        )
        self.enquiry_editor.pack(fill="x", padx=18, pady=(8, 6))
        actions = tk.Frame(self, bg=BG)
        actions.pack(fill="x", padx=18)
        tk.Button(
            actions, text="Dodaj PDF", command=self._attach_pdf,
            bg="#29253A", fg=FG, relief="flat", padx=12, pady=6,
        ).pack(side="left")
        tk.Button(
            actions, text="Zapisz treść lokalnie", command=self._save_enquiry,
            bg="#29253A", fg=FG, relief="flat", padx=12, pady=6,
        ).pack(side="left", padx=(8, 0))
        tk.Button(
            actions, text="Podgląd danych", command=self._preview_enquiry,
            bg="#29253A", fg=FG, relief="flat", padx=12, pady=6,
        ).pack(side="right")
        self.notice = self._label(
            self,
            "Model rozmowny nie jest skonfigurowany — wiadomości są lokalne."
            if not (self.conversation is not None and self.conversation.status().provider_connected)
            else "Model rozmowny połączony. Załączone dokumenty nie są wysyłane automatycznie.",
            size=9, color=MUTED,
        )
        self.notice.pack(fill="x", padx=18, pady=(8, 12))
        self.entry.focus_set()

    def _start_discovery(self, *, revision: int):
        """Run only the read-only local tool requested in chat."""
        if self.discover_windowhub is None:
            self.chat.agent_message(
                "Nie mam w tej sesji podłączonego narzędzia wykrywania programów. "
                "Nie wykonałem wyszukiwania.", based_on_revision=revision,
            )
            return
        if self._discovery_active:
            self.chat.agent_message(
                "Wyszukiwanie WindowHub już trwa. Nie uruchamiam drugiego.",
                based_on_revision=revision,
            )
            return
        self._discovery_active = True
        self.notice.configure(text="Sprawdzam uruchomione programy Windows…")

        def worker():
            try:
                lines = tuple(self.discover_windowhub())
            except Exception:
                lines = ("WINDOWHUB_DISCOVERY=FAILED",)
            try:
                self._discovery_queue.put_nowait((revision, lines))
            except Exception:
                pass

        Thread(target=worker, daemon=True).start()

    def _poll_discovery(self):
        try:
            revision, lines = self._discovery_queue.get_nowait()
        except Empty:
            return
        self._discovery_active = False
        # A newer user request supersedes any slow result.
        self.chat.agent_message(
            windowhub_discovery_answer(lines),
            based_on_revision=revision,
        )
        self._refresh_messages()
        self.notice.configure(text="Lokalne wyszukiwanie zakończone — bez sterowania pulpitem.")

    def _history_to_bottom(self):
        self.history.yview_moveto(1.0)

    def _history_bottom_shortcut(self, event):
        self._history_to_bottom()
        return "break"

    def _history_top_shortcut(self, event):
        self.history.yview_moveto(0.0)
        return "break"

    def _history_mousewheel(self, event):
        units = scroll_history_lines(event.delta)
        if units:
            self.history.yview_scroll(units, "units")
        return "break"

    def _history_mousewheel_linux(self, event):
        self.history.yview_scroll(-3 if event.num == 4 else 3, "units")
        return "break"

    def _append(self, author: str, content: str):
        # Do not steal the user's position when reviewing an older answer.
        # A fresh conversation initially follows incoming messages.
        stay_at_bottom = chat_view_near_bottom(self.history.yview()[1])
        self.history.configure(state="normal")
        self.history.insert("end", author + "\n", ("author",))
        self.history.insert("end", content + "\n\n")
        self.history.tag_configure("author", foreground=PURPLE)
        self.history.configure(state="disabled")
        if stay_at_bottom:
            self._history_to_bottom()

    def _keyboard_send(self, event):
        self._send()
        return "break"

    def _send(self):
        text = self.entry.get("1.0", "end-1c").strip()
        decision = chat_intake_decision(text)
        if decision == "empty":
            return
        if decision == "long_enquiry":
            if len(text) > 100_000:
                messagebox.showwarning(
                    "Za długie zapytanie",
                    "Zapytanie przekracza limit 100 000 znaków. Skróć je lub dodaj PDF. Tekst pozostaje w polu rozmowy.",
                    parent=self,
                )
                return
            if not messagebox.askyesno(
                "Długie zapytanie klienta",
                f"To {len(text)} znaków, a jedna wiadomość rozmowy może mieć maksymalnie "
                f"{MissionChat.MAX_MESSAGE_CHARS}.\n\n"
                "Przenieść pełną treść do sekcji ZAPYTANIE KLIENTA / PDF? "
                "Nie zostanie wysłana do AI ani WindowHub.",
                parent=self,
            ):
                return
            # Do not silently overwrite a draft already present in the intake.
            existing = self.enquiry_editor.get("1.0", "end-1c").strip()
            if existing and existing != text:
                self.enquiry_editor.insert("end", "\n\n" + text)
            else:
                self.enquiry_editor.delete("1.0", "end")
                self.enquiry_editor.insert("1.0", text)
            try:
                self.enquiry.set_text(self.enquiry_editor.get("1.0", "end-1c"))
            except EnquiryInputError as exc:
                messagebox.showwarning(
                    "Zapytanie nie zostało przeniesione",
                    "Dane przekraczają limit schowka zapytań. Treść wiadomości pozostaje w polu. "
                    + str(exc),
                    parent=self,
                )
                return
            self.entry.delete("1.0", "end")
            self._update_sources()
            self.notice.configure(
                text="Pełne zapytanie przeniesione do dokumentów (lokalnie). "
                     "W polu rozmowy wpisz krótkie polecenie."
            )
            return
        try:
            message = self.chat.user_message(text)
        except (ValueError, RuntimeError) as exc:
            messagebox.showwarning(
                "Wiadomość nieprzyjęta",
                "Nie udało się dodać wiadomości. Sprawdź tekst lub limit rozmowy. "
                + str(exc),
                parent=self,
            )
            return
        self.entry.delete("1.0", "end")
        self._refresh_messages()
        if requested_local_tool(text) == "discover_windowhub":
            self._start_discovery(revision=message.mission_revision)
            return
        if (self.conversation is not None
                and self.conversation.submit_current_message(message.message_id)):
            self.notice.configure(text="NaviMind przygotowuje odpowiedź…")
        else:
            self.notice.configure(
                text="Wiadomość zapisana. Model AI nie jest podłączony — nie otrzymasz jeszcze odpowiedzi."
            )

    def _dictate(self):
        try:
            if not start_windows_dictation(self.entry):
                self.notice.configure(text="Dyktowanie Windows dostępne wyłącznie na Windows.")
                return
            self.notice.configure(
                text="Dyktowanie Windows: mów do mikrofonu, sprawdź tekst i kliknij Wyślij."
            )
        except (OSError, AttributeError, RuntimeError) as exc:
            self.notice.configure(
                text="Dyktowanie Windows niedostępne: " + type(exc).__name__
            )

    def _save_enquiry(self):
        text = self.enquiry_editor.get("1.0", "end-1c")
        try:
            self.enquiry.set_text(text)
        except EnquiryInputError as exc:
            messagebox.showwarning("Treść zapytania", str(exc), parent=self)
            return
        self._update_sources()
        self.notice.configure(text="Zapytanie zapisane w pamięci sesji, bez wysyłania do AI.")

    def _attach_pdf(self):
        path = filedialog.askopenfilename(
            parent=self, title="Dodaj zapytanie PDF",
            filetypes=[("Dokument PDF", "*.pdf")],
        )
        if not path:
            return
        try:
            source = self.enquiry.add_pdf(path)
        except (EnquiryInputError, OSError) as exc:
            messagebox.showwarning("PDF nieodczytany", str(exc), parent=self)
            return
        self._update_sources()
        if source.needs_ocr or source.truncated:
            self.notice.configure(
                text="PDF dodany częściowo. Wymagana kontrola brakujących/skanowanych stron."
            )
        else:
            self.notice.configure(text="PDF odczytany lokalnie. Treść nie została wysłana do AI.")

    def _update_sources(self):
        stats = self.enquiry.status()
        self.source_status.configure(
            text=f"{stats['pdf_count']} PDF · {stats['characters']} znaków"
        )

    def _preview_enquiry(self):
        window = tk.Toplevel(self)
        window.title("NaviMind • Podgląd zapytania (tylko odczyt)")
        window.geometry("720x540")
        frame = tk.Frame(window, bg=CARD)
        frame.pack(fill="both", expand=True, padx=8, pady=8)
        scrollbar = tk.Scrollbar(frame, orient="vertical")
        scrollbar.pack(side="right", fill="y")
        area = tk.Text(
            frame, wrap="word", font=("Segoe UI", 10),
            bg=CARD, fg=FG, yscrollcommand=scrollbar.set,
        )
        area.pack(side="left", fill="both", expand=True)
        scrollbar.configure(command=area.yview)
        preview = self.enquiry.preview(limit=10_000)
        unsaved = self.enquiry_editor.get("1.0", "end-1c").strip()
        if unsaved and unsaved != self.enquiry.pasted_text:
            preview = "[NIEZAPISANA TREŚĆ W POLU — użyj 'Zapisz treść lokalnie']\n\n" + preview
        area.insert("1.0", preview)
        area.configure(state="disabled")

    def _refresh_messages(self):
        snapshot = self.chat.snapshot()
        for message in snapshot.messages:
            if message.message_id <= self.last_id:
                continue
            name = {
                MessageRole.HUMAN: "Ty",
                MessageRole.AGENT: "NaviMind",
                MessageRole.SYSTEM: "System",
            }[message.role]
            self._append(name, message.text)
            self.last_id = message.message_id

    def _poll(self):
        if not self.winfo_exists():
            return
        self._refresh_messages()
        self._poll_discovery()
        if self.conversation is not None:
            status = self.conversation.status()
            if status.active:
                self.notice.configure(text="NaviMind przygotowuje odpowiedź…")
            elif status.last_error:
                self.notice.configure(text=friendly_chat_error(status.last_error))
                self.provider_indicator.configure(text="MODEL AI: BŁĄD ODPOWIEDZI", fg=GOLD)
            elif status.provider_connected:
                self.provider_indicator.configure(text="MODEL AI: GOTOWY", fg="#93D9BE")
        self.after(350, self._poll)
