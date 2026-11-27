"""Integrated NaviMind workspace: chat, enquiry/PDF intake and Windows dictation.

Every submission goes to the same MissionChat / LiveMissionConversation as
the verified WindowHub host. No uploaded document is sent anywhere merely by
being attached. Native control remains observation-only in the current host.
"""
from __future__ import annotations

import ctypes
import os
import tkinter as tk
from tkinter import filedialog, messagebox

from app.agent.runtime.navimind_enquiry_inbox import EnquiryInputError, LocalEnquiryInbox
from app.agent.runtime.navimind_mission_chat import MessageRole, MissionChat


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
from tools.run_navimind_control_panel import BG, CARD, FG, MUTED, PURPLE, GOLD, STROKE, SURFACE, GREEN


GATEWAY_ERROR_LABELS = {
    "chat_authentication_failed_401": "CHAT 401: dostawca odrzucił klucz. Uruchom lokalnie: python -m tools.configure_navimind_chat --setup-gateway",
    "chat_gateway_credits_or_budget_402": "Błąd AI 402: brak środków albo przekroczony budżet Gateway.",
    "chat_gateway_access_denied_403": "Błąd AI 403: Vercel odmawia dostępu; sprawdź weryfikację konta.",
    "chat_model_or_endpoint_not_found_404": "Błąd AI 404: model lub adres API jest niedostępny.",
    "chat_gateway_rate_limited_429": "Błąd AI 429: limit żądań; spróbuj później.",
    "chat_transport_unavailable": "Błąd połączenia AI: sieć, TLS lub przekroczony czas odpowiedzi.",
    "chat_provider_unavailable_503": "Błąd AI 503: usługa modelu chwilowo niedostępna.",
    "chat_provider_timeout_504": "Błąd AI 504: serwer modelu nie odpowiedział.",
    "chat_model_unavailable_or_invalid_response": "Model nie zwrócił poprawnej odpowiedzi.",
    "chat_unexpected_response_error": "Nieoczekiwany błąd odpowiedzi modelu.",
    "document_revoked_requires_new_request": "Dostęp do dokumentu cofnięty. Wpisz polecenie ponownie.",
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


def chat_key_action(*, shift: bool, control: bool = False) -> str:
    """One-line submission, with Shift+Enter reserved for multiline drafts."""
    return "newline" if shift else "send"


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
                 discover_windowhub=None, on_document_revoke=None,
                 current_work_continuation=None):
        super().__init__(parent, bg=BG)
        self.chat = chat
        self.conversation = conversation
        self.enquiry = enquiry or LocalEnquiryInbox()
        self.last_id = 0
        self.discover_windowhub = discover_windowhub
        self.on_document_revoke = on_document_revoke
        self.current_work_continuation = current_work_continuation
        self._build()
        self._poll()

    def _label(self, parent, value, *, size=10, color=FG, bold=False):
        return tk.Label(
            parent, text=value, bg=parent.cget("bg"), fg=color,
            font=("Segoe UI Semibold" if bold else "Segoe UI", size),
            anchor="w",
        )

    def _build(self):
        header = tk.Frame(self, bg=BG)
        header.pack(fill="x", padx=24, pady=(20, 13))
        title_column = tk.Frame(header, bg=BG)
        title_column.pack(side="left", fill="x", expand=True)
        tk.Label(
            title_column, text="NaviMind", bg=BG, fg=FG,
            font=("Segoe UI Semibold", 22), anchor="w",
        ).pack(fill="x")
        self._label(
            title_column, "Inteligentny workspace  /  Rozmowa i zapytania",
            size=10, color=MUTED,
        ).pack(fill="x", pady=(2, 0))
        tk.Label(
            header, text="  ●  LOKALNY HOST  ", bg=SURFACE,
            fg=GREEN, font=("Segoe UI Semibold", 9), padx=10,
            pady=9,
        ).pack(side="right")

        top = tk.Frame(self, bg=CARD)
        top.pack(fill="both", expand=True, padx=24, pady=(0, 12))
        chat_heading = tk.Frame(top, bg=CARD)
        chat_heading.pack(fill="x", padx=16, pady=(15, 7))
        self._label(chat_heading, "ROZMOWA", size=11, color=FG, bold=True).pack(side="left")
        active = self.conversation is not None and self.conversation.status().provider_connected
        self.provider_indicator = self._label(
            chat_heading,
            "MODEL AI: PODŁĄCZONY" if active else "MODEL AI: NIEPODŁĄCZONY",
            size=9, color=GREEN if active else GOLD,
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
            relief="flat", font=("Segoe UI", 11), state="disabled",
            padx=16, pady=12, height=8,
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
        self._install_history_copy_menu()

        history_actions = tk.Frame(top, bg=CARD)
        history_actions.pack(fill="x", padx=12, pady=(0, 8))
        self._label(
            history_actions, "Przewijaj historię kółkiem myszy lub paskiem po prawej.",
            size=8, color=MUTED,
        ).pack(side="left")
        tk.Button(
            history_actions, text="Kopiuj ostatnią odpowiedź",
            command=self._copy_latest_agent_reply,
            fg=FG, bg=SURFACE, relief="flat", padx=10, pady=5,
        ).pack(side="right", padx=(0, 8))
        tk.Button(
            history_actions, text="↓ Najnowsze", command=self._history_to_bottom,
            fg=FG, bg=SURFACE, relief="flat", padx=12, pady=5,
        ).pack(side="right")

        self._label(
            self, "TWOJE POLECENIE  ·  Enter wyślij  ·  Shift+Enter nowa linia",
            size=9, color=MUTED,
        ).pack(fill="x", padx=24)
        self.entry = tk.Text(
            self, wrap="word", bg=SURFACE, fg=FG, height=3,
            insertbackground=FG, font=("Segoe UI", 11), relief="flat",
            padx=14, pady=11,
        )
        self.entry.pack(fill="x", padx=24, pady=(7, 10))
        self.entry.bind("<Return>", self._keyboard_enter)
        self.entry.bind("<KP_Enter>", self._keyboard_enter)
        self.entry.bind("<Shift-Return>", self._keyboard_newline)
        self.entry.bind("<Control-Return>", self._keyboard_send)
        self._install_edit_context_menu(self.entry)

        buttons = tk.Frame(self, bg=BG)
        buttons.pack(fill="x", padx=24, pady=(0, 14))
        self.mic = tk.Button(
            buttons, text="🎙 Dyktuj (Win+H)", command=self._dictate,
            fg=FG, bg=SURFACE, relief="flat",
            font=("Segoe UI Semibold", 10), padx=12, pady=8,
        )
        self.mic.pack(side="left")
        if not windows_dictation_available():
            self.mic.configure(state="disabled")
        tk.Button(
            buttons, text="Wyślij", command=self._send,
            fg="#151020", bg=PURPLE, relief="flat",
            font=("Segoe UI Semibold", 11), padx=25, pady=9,
        ).pack(side="right")

        tk.Frame(self, height=1, bg=STROKE).pack(fill="x", padx=24, pady=(4, 12))
        heading = tk.Frame(self, bg=BG)
        heading.pack(fill="x", padx=24)
        self._label(
            heading, "DOKUMENTY KLIENTA", size=11, color=FG, bold=True,
        ).pack(side="left")
        self.source_status = self._label(heading, "Brak dokumentów", size=9, color=MUTED)
        self.source_status.pack(side="right")
        self.document_approval_indicator = self._label(
            self, "AI: dokument lokalny — nieudostępniony",
            size=9, color=GOLD,
        )
        self.document_approval_indicator.pack(fill="x", padx=24, pady=(2, 0))
        self._label(
            self, "Wklej zapytanie klienta. Polecenia dla NaviMind wpisuj w rozmowie wyżej.",
            size=9, color=MUTED,
        ).pack(fill="x", padx=24, pady=(6, 0))
        enquiry_box = tk.Frame(self, bg=CARD)
        enquiry_box.pack(fill="x", padx=24, pady=(10, 8))
        self.enquiry_scrollbar = tk.Scrollbar(
            enquiry_box, orient="vertical", width=13, takefocus=True,
        )
        self.enquiry_scrollbar.pack(side="right", fill="y")
        self.enquiry_editor = tk.Text(
            enquiry_box, height=4, wrap="word", bg=CARD, fg=FG, insertbackground=FG,
            relief="flat", font=("Segoe UI", 10), padx=14, pady=10,
            yscrollcommand=self.enquiry_scrollbar.set,
        )
        self.enquiry_editor.pack(side="left", fill="both", expand=True)
        self.enquiry_scrollbar.configure(command=self.enquiry_editor.yview)
        self._install_edit_context_menu(self.enquiry_editor)
        # Text widgets already support mouse-wheel, keyboard navigation and
        # selecting/copying their contents; preserve those native bindings.
        actions = tk.Frame(self, bg=BG)
        actions.pack(fill="x", padx=24)
        tk.Button(
            actions, text="Dodaj PDF", command=self._attach_pdf,
            bg=SURFACE, fg=FG, relief="flat", padx=12, pady=6,
        ).pack(side="left")
        tk.Button(
            actions, text="Wklej ze schowka Windows", command=self._paste_windows_clipboard,
            bg=SURFACE, fg=FG, relief="flat", padx=12, pady=6,
        ).pack(side="left", padx=(8, 0))
        tk.Button(
            actions, text="Zapisz treść lokalnie", command=self._save_enquiry,
            bg="#29253A", fg=FG, relief="flat", padx=12, pady=6,
        ).pack(side="left", padx=(8, 0))
        tk.Button(
            actions, text="Podgląd danych", command=self._preview_enquiry,
            bg=SURFACE, fg=FG, relief="flat", padx=12, pady=6,
        ).pack(side="right")
        sharing_row = tk.Frame(self, bg=BG)
        sharing_row.pack(fill="x", padx=24, pady=(8, 0))
        self.share_document_button = tk.Button(
            sharing_row, text="Przeanalizuj dokument w NaviMind",
            command=self._share_document_with_ai,
            bg=PURPLE, fg="#111319", relief="flat", padx=12, pady=8,
            font=("Segoe UI Semibold", 10),
        )
        self.share_document_button.pack(side="left")
        tk.Button(
            sharing_row, text="Cofnij dostęp AI",
            command=self._revoke_document_access,
            bg=SURFACE, fg=FG, relief="flat", padx=10, pady=8,
        ).pack(side="left", padx=(9, 0))
        self.notice = self._label(
            self,
            "Brak połączenia AI: sprawdź NAVIMIND_CHAT_URL / MODEL / API_KEY w bieżącej sesji. Wiadomości pozostają lokalne."
            if not (self.conversation is not None and self.conversation.status().provider_connected)
            else "Model rozmowny połączony. Załączone dokumenty nie są wysyłane automatycznie.",
            size=9, color=MUTED,
        )
        self.notice.pack(fill="x", padx=24, pady=(11, 15))
        self.entry.focus_set()

    def _copy_to_clipboard(self, content: str):
        """Explicit local clipboard action; never sends text to AI."""
        self.clipboard_clear()
        self.clipboard_append(content)
        self.update_idletasks()

    def _copy_history_selection(self):
        try:
            selection = self.history.get("sel.first", "sel.last")
        except tk.TclError:
            return False
        if not selection:
            return False
        self._copy_to_clipboard(selection)
        return True

    def _copy_latest_agent_reply(self):
        messages = self.chat.snapshot().messages
        for message in reversed(messages):
            if message.role == MessageRole.AGENT:
                self._copy_to_clipboard(message.text)
                self.notice.configure(text="Ostatnia odpowiedź NaviMind skopiowana.")
                return
        self.notice.configure(text="Brak odpowiedzi NaviMind do skopiowania.")

    def _install_history_copy_menu(self):
        """Copy from disabled/read-only conversation history via right click."""
        menu = tk.Menu(self.history, tearoff=False)
        menu.add_command(label="Kopiuj zaznaczenie",
                         command=self._copy_history_selection)
        menu.add_command(label="Kopiuj ostatnią odpowiedź",
                         command=self._copy_latest_agent_reply)
        menu.add_separator()
        menu.add_command(label="Zaznacz całą rozmowę",
                         command=lambda: (
                             self.history.tag_add("sel", "1.0", "end-1c"),
                             self.history.focus_set(),
                         ))

        def show(event):
            # Right click should not alter a mouse-selected text range.
            try:
                has_selection = bool(self.history.get("sel.first", "sel.last"))
            except tk.TclError:
                has_selection = False
            menu.entryconfigure(0, state="normal" if has_selection else "disabled")
            try:
                menu.tk_popup(event.x_root, event.y_root)
            finally:
                menu.grab_release()
            return "break"

        self.history.bind("<Button-3>", show)
        self._history_copy_menu = menu

    def _install_edit_context_menu(self, widget):
        """Windows-style right-click edit menu scoped to this Tk Text widget.

        Only local clipboard operations. No chat submission, document consent,
        model request or WindowHub input is triggered by these actions.
        """
        menu = tk.Menu(widget, tearoff=False)
        menu.add_command(label="Wytnij", command=lambda: widget.event_generate("<<Cut>>"))
        menu.add_command(label="Kopiuj", command=lambda: widget.event_generate("<<Copy>>"))
        menu.add_command(label="Wklej", command=lambda: widget.event_generate("<<Paste>>"))
        menu.add_separator()
        menu.add_command(label="Zaznacz wszystko", command=lambda: (
            widget.tag_add("sel", "1.0", "end-1c"),
            widget.mark_set("insert", "end-1c"),
            widget.see("insert"),
            widget.focus_set(),
        ))

        def show(event):
            widget.focus_set()
            try:
                menu.tk_popup(event.x_root, event.y_root)
            finally:
                menu.grab_release()
            return "break"

        widget.bind("<Button-3>", show)
        # Keep the menu alive for the full widget lifetime.
        if not hasattr(self, "_edit_context_menus"):
            self._edit_context_menus = []
        self._edit_context_menus.append(menu)

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
        human = author.casefold().strip() in ("ty", "user", "użytkownik")
        role_tag = "human_label" if human else "agent_label"
        body_tag = "human_body" if human else "agent_body"
        self.history.insert("end", author.upper() + "\n", (role_tag,))
        self.history.insert("end", content + "\n\n", (body_tag,))
        self.history.tag_configure("human_label", foreground=GOLD,
                                   font=("Segoe UI Semibold", 9), spacing1=6)
        self.history.tag_configure("agent_label", foreground=PURPLE,
                                   font=("Segoe UI Semibold", 9), spacing1=6)
        self.history.tag_configure("human_body", foreground=FG,
                                   spacing2=4, spacing3=10)
        self.history.tag_configure("agent_body", foreground=FG,
                                   spacing2=4, spacing3=12)
        self.history.tag_configure("author", foreground=PURPLE)
        self.history.configure(state="disabled")
        if stay_at_bottom:
            self._history_to_bottom()

    def _keyboard_newline(self, event):
        # Native Tk Text inserts the newline for Shift+Return.
        return None

    def _keyboard_enter(self, event):
        if chat_key_action(shift=bool(event.state & 0x0001)) == "newline":
            return None
        self._send()
        return "break"

    def _keyboard_send(self, event):
        self._send()
        return "break"

    @staticmethod
    def _is_continue_current_mission_request(text):
        """Acknowledge a short follow-up without invalidating active mission.

        Never treat free-form editing instructions as a harmless continuation.
        Explicit local operator Resume remains required for any GUI action.
        """
        import re
        if not isinstance(text, str) or len(text) > 140:
            return False
        t = re.sub(r"[, ]+", " ", " ".join(text.casefold().split()))
        t = t.strip(" .!?")
        from app.agent.runtime.navimind_live_conversation import (
            explicit_background_work_request, explicit_service_exclusion_correction,
        )
        if explicit_background_work_request(text) or explicit_service_exclusion_correction(text):
            return True
        return bool(re.fullmatch(
            r"(?:(?:ok|okej|dobrze|tak) )?(?:kontynuuj(?: prac[eę])?|"
            r"wzn[oó]w(?: prac[eę])?|wykonaj nast[eę]pny krok|"
            r"przejd[zź] do nast[eę]pnego kroku|dalej|co dalej|"
            r"zr[oó]b (?:t[eę] )?ofert[eę]|gotowe|zrobione|"
            r"wybra[łl]em klienta|wybra[łl]am klienta|klient wybrany|"
            r"ustawi[łl](?:em|am) preferencje|preferencje ustawione|"
            r"jestem w edytorze|potwierdzam klienta|tak|ok|okej)",
            t,
        ))

    def _send(self):
        text = self.entry.get("1.0", "end-1c").strip()
        decision = chat_intake_decision(text)
        if decision == "empty":
            return
        if self._is_continue_current_mission_request(text):
            reply = (self.current_work_continuation(text)
                     if self.current_work_continuation is not None else None)
            if reply is not None:
                revision, message = reply
                self.entry.delete("1.0", "end")
                self.notice.configure(text=message)
                self.chat.agent_message(message, based_on_revision=revision)
                self._refresh_messages()
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
            if self.conversation is not None:
                self._drop_document_consent()
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

    def _approved_mission_snapshot(self, excerpt: str) -> str:
        """Freeze PDF analysis on Tk thread at the moment of explicit consent.

        A later background V2 worker must NOT re-read mutable input widgets
        or newly added PDFs under an older approval epoch.
        """
        from app.agent.runtime.navimind_enquiry_evidence_bridge import (
            summarize_full_approved_inbox,
        )
        digest = summarize_full_approved_inbox(
            self.enquiry, approved=True, limit=2800,
        )
        return (digest + "\n\n" + excerpt)[:7500]

    def _handle_model_document_consent(self, request):
        """Tk-thread approval of a tool requested by the LLM.

        The model does NOT get the document until the operator confirms
        sending the bounded excerpt to the configured external AI Gateway.
        """
        revision, message_id = request
        if self.chat.snapshot().mission_revision != revision:
            return
        draft = self.enquiry_editor.get("1.0", "end-1c").strip()
        try:
            if draft and draft != self.enquiry.pasted_text:
                self.enquiry.set_text(draft)
                self._update_sources()
            excerpt = self.enquiry.model_context()
        except (EnquiryInputError, ValueError):
            self.chat.agent_message(
                "Nie ma jeszcze odczytanego dokumentu do analizy. "
                "Dodaj PDF lub wklej zapytanie do lokalnego schowka.",
                based_on_revision=revision,
            )
            self._refresh_messages()
            return
        stats = self.enquiry.status()
        agreed = messagebox.askyesno(
            "NaviMind potrzebuje dostępu do dokumentu",
            "Poprosiłeś o analizę dokumentu. NaviMind znalazł go "
            "w lokalnym schowku. Aby model mógł odczytać parametry, "
            "wyślemy fragment odczytanego tekstu do dostawcy "
            "AI Gateway. Może zawierać dane osobowe klienta.\n\n"
            f"PDF: {stats['pdf_count']}; fragment: {len(excerpt)} znaków.\n\n"
            "Po osobnym poleceniu przygotowania oferty silnik V2 może "
            "otrzymać również lokalnie sporządzone zestawienie z całego "
            "odczytanego tekstu tych PDF (łącznie maks. 7500 znaków "
            "z zatwierdzonym fragmentem). Nie wysyłamy pełnych plików PDF. "
            "Zgoda obejmuje dalsze pytania w tej sesji, chyba że "
            "wybierzesz „Cofnij dostęp AI”. Zgoda na analizę NIE jest "
            "zgodą na kliknięcia, zapis ani wysyłkę oferty.\n\n"
            "Udostępnić fragment do analizy?",
            parent=self,
        )
        # Dialog can outlive the request: never approve a stale mission.
        if self.chat.snapshot().mission_revision != revision:
            return
        if not agreed:
            self.conversation.publish_document_consent_denied(revision)
            self._refresh_messages()
            return
        try:
            from app.agent.runtime.navimind_position_ledger import (
                build_position_manifest,
            )
            self.conversation.approve_document_context(
                excerpt,
                mission_evidence=self._approved_mission_snapshot(excerpt),
                position_manifest=build_position_manifest(self.enquiry),
            )
        except (RuntimeError, ValueError):
            self.notice.configure(text="Nie udało się przyznać dostępu AI.")
            return
        if self.conversation.submit_current_message(message_id):
            self.notice.configure(
                text="Udostępniono fragment PDF; NaviMind analizuje źródło…"
            )
        else:
            self._drop_document_consent()
            self.notice.configure(
                text="Nie można ponowić analizy. Dokument nie został wysłany."
            )

    def _drop_document_consent(self):
        """Revoke provider context AND any previously armed native work."""
        if self.conversation is not None:
            self.conversation.revoke_document_context()
        callback = getattr(self, "on_document_revoke", None)
        if callback is not None:
            callback()

    def _revoke_document_access(self):
        self._drop_document_consent()
        self.notice.configure(
            text="Dostęp AI do dokumentów cofnięty dla kolejnych wiadomości. "
                 "Wcześniejszych żądań wysłanych do Gateway nie można wycofać."
        )

    def _share_document_with_ai(self):
        """Only an explicit operator gesture can share local PDF/text."""
        if self.conversation is None or not self.conversation.status().provider_connected:
            self.notice.configure(text="Model AI nie jest podłączony. Dokument pozostał lokalny.")
            return
        draft = self.enquiry_editor.get("1.0", "end-1c").strip()
        try:
            if draft and draft != self.enquiry.pasted_text:
                self.enquiry.set_text(draft)
                self._update_sources()
            context = self.enquiry.model_context()
        except EnquiryInputError:
            self.notice.configure(text="Najpierw dodaj dokument PDF lub zapytanie klienta.")
            return
        except ValueError:
            self.notice.configure(text="Dokument nie może zostać przygotowany do analizy.")
            return
        source_status = self.enquiry.status()
        if not messagebox.askyesno(
            "Udostępnić dokument modelowi AI?",
            "Wyślesz do skonfigurowanego dostawcy AI Gateway tekst z "
            "lokalnego schowka (również dane kontaktowe występujące "
            "w PDF).\n\n"
            f"Dokumenty PDF: {source_status['pdf_count']}; "
            f"fragment przekazywany modelowi: {len(context)} znaków.\n\n"
            "Po osobnym poleceniu wykonania oferty silnik V2 może także "
            "otrzymać lokalnie opracowany skrót całego odczytanego tekstu "
            "PDF — łącznie maks. 7500 znaków z zatwierdzonym fragmentem. "
            "Zgoda obowiązuje również w kolejnych wiadomościach tej "
            "sesji, dopóki jej nie cofniesz albo nie zmienisz dokumentów. "
            "Nie stanowi zgody na sterowanie, zapis ani wysyłkę oferty.\n\n"
            "Udostępnić dokument do analizy?",
            parent=self,
        ):
            return
        prompt = (
            "Przeanalizuj udostępnione zapytanie klienta/PDF i napisz po polsku "
            "co rzeczywiście zawiera: pozycje, wymiary, profile, kolory, "
            "szyby, okucia oraz brakujące dane. "
            "Opieraj się tylko na odczytanym tekście; "
            "nie myl PDF z bieżącym ekranem WindowHub."
        )
        try:
            from app.agent.runtime.navimind_position_ledger import (
                build_position_manifest,
            )
            self.conversation.approve_document_context(
                context,
                mission_evidence=self._approved_mission_snapshot(context),
                position_manifest=build_position_manifest(self.enquiry),
            )
            message = self.chat.user_message(prompt)
        except (ValueError, RuntimeError):
            self._drop_document_consent()
            self.notice.configure(text="Nie udało się rozpocząć analizy dokumentu.")
            return
        self._refresh_messages()
        if self.conversation.submit_current_message(message.message_id):
            self.notice.configure(
                text="Udostępniono fragment dokumentu AI Gateway na potrzeby "
                     "analizy i kolejnych pytań w tej sesji."
            )
        else:
            self._drop_document_consent()
            self.notice.configure(text="Nie udało się wysłać dokumentu do analizy AI.")

    def _paste_windows_clipboard(self):
        """Import clipboard text only on an explicit user gesture.

        Tk owns clipboard access on the main GUI thread. Never poll clipboard
        or transmit it to the model without the existing document consent.
        """
        try:
            content = self.clipboard_get()
        except (tk.TclError, UnicodeError):
            self.notice.configure(text="Schowek nie zawiera dostępnego tekstu.")
            return
        if not isinstance(content, str) or not content.strip():
            self.notice.configure(text="Schowek nie zawiera tekstowego zapytania.")
            return
        content = content.strip()
        current = self.enquiry_editor.get("1.0", "end-1c").strip()
        combined = current + "\n\n" + content if current and current != content else content
        try:
            from app.agent.runtime.navimind_enquiry_inbox import validate_pasted_enquiry
            validated = validate_pasted_enquiry(combined)
        except EnquiryInputError:
            self.notice.configure(text="Tekst ze schowka przekracza limit 100 000 znaków.")
            return
        self.enquiry_editor.delete("1.0", "end")
        self.enquiry_editor.insert("1.0", validated)
        self.enquiry.set_text(validated)
        if self.conversation is not None:
            self._drop_document_consent()
        self._update_sources()
        self.notice.configure(
            text="Tekst ze schowka skopiowany lokalnie. Nie został wysłany do modelu."
        )

    def _save_enquiry(self):
        text = self.enquiry_editor.get("1.0", "end-1c")
        try:
            self.enquiry.set_text(text)
        except EnquiryInputError as exc:
            messagebox.showwarning("Treść zapytania", str(exc), parent=self)
            return
        if self.conversation is not None:
            self._drop_document_consent()
        self._update_sources()
        self.notice.configure(text="Zapytanie zapisane lokalnie. Udostępnij je AI tylko świadomie.")

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
        if self.conversation is not None:
            self._drop_document_consent()
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
        if self.conversation is not None:
            pending = self.conversation.take_pending_document_approval()
            if pending is not None:
                self._handle_model_document_consent(pending)
            approved = self.conversation.document_context_active()
            self.document_approval_indicator.configure(
                text=("AI: dokument udostępniony w tej sesji"
                      if approved else
                      "AI: dokument lokalny — kliknij „Przeanalizuj dokument w NaviMind”"),
                fg=GREEN if approved else GOLD,
            )
            status = self.conversation.status()
            if status.active:
                self.notice.configure(text="NaviMind przygotowuje odpowiedź…")
            elif status.last_error:
                self.notice.configure(text=friendly_chat_error(status.last_error))
                self.provider_indicator.configure(text="MODEL AI: BŁĄD ODPOWIEDZI", fg=GOLD)
            elif status.provider_connected:
                self.provider_indicator.configure(text="MODEL AI: GOTOWY", fg="#93D9BE")
        self.after(350, self._poll)
