"""Conversation window bound to the same local host as NaviMind panel.

Accepts messages and immediately pauses any current agent plan. This stage
does not call an LLM, auto-interpret instructions or edit WindowHub.
"""
from __future__ import annotations

import tkinter as tk
from tkinter import messagebox

from app.agent.runtime.navimind_mission_chat import MissionChat, MessageRole
from app.agent.runtime.navimind_live_conversation import LiveMissionConversation

BG = "#101019"
CARD = "#1B1B29"
INK = "#F5F1FA"
MUTED = "#A6A1B7"
PURPLE = "#A989F9"
GOLD = "#E6C789"


class NaviMindChatWindow(tk.Toplevel):
    def __init__(self, parent: tk.Misc, inbox: MissionChat,
                 conversation: LiveMissionConversation | None = None):
        super().__init__(parent)
        self.inbox = inbox
        self.conversation = conversation
        self.title("NaviMind • Rozmowa podczas zadania")
        self.geometry("480x565")
        self.minsize(425, 490)
        self.configure(bg=BG)
        self.last_id = 0
        self._build()
        self._refresh()
        if self.conversation is not None:
            status = self.conversation.status()
            self.hint.configure(
                text="NaviMind przygotowuje odpowiedź…" if status.active
                else ("Model rozmowy niedostępny — zadanie pozostaje bez zmian"
                      if status.last_error and status.provider_connected else
                      "Ctrl+Enter — wyślij")
            )
        self.after(350, self._poll)

    def _label(self, parent, text, *, color=INK, size=10, bold=False, **kwargs):
        return tk.Label(
            parent, text=text, fg=color, bg=parent.cget("bg"),
            font=("Segoe UI Semibold" if bold else "Segoe UI", size), **kwargs,
        )

    def _build(self):
        top = tk.Frame(self, bg=BG, padx=20, pady=17)
        top.pack(fill="x")
        self._label(top, "Rozmowa z NaviMind", size=16, bold=True).pack(anchor="w")
        self._label(
            top, "Wiadomość wstrzymuje stare decyzje. Zmiany wymagają weryfikacji.",
            color=MUTED, size=9, wraplength=420, justify="left",
        ).pack(anchor="w", pady=(6, 0))

        chat_frame = tk.Frame(self, bg=CARD, padx=8, pady=8)
        chat_frame.pack(fill="both", expand=True, padx=18, pady=(0, 12))
        self.history = tk.Text(
            chat_frame, bg=CARD, fg=INK, relief="flat", bd=0,
            highlightthickness=0, font=("Segoe UI", 10),
            wrap="word", padx=12, pady=12, state="disabled",
            insertbackground=INK, selectbackground="#51406A",
        )
        self.history.pack(fill="both", expand=True)
        self.history.tag_configure("user", foreground="#D9C4FF",
                                   font=("Segoe UI Semibold", 10),
                                   spacing1=14)
        self.history.tag_configure("agent", foreground="#96D5C6",
                                   font=("Segoe UI Semibold", 10),
                                   spacing1=14)
        self.history.tag_configure("system", foreground=GOLD,
                                   font=("Segoe UI Semibold", 10),
                                   spacing1=14)
        self.history.tag_configure("body", foreground=INK, spacing3=7)
        self.history.tag_configure("notice", foreground=MUTED,
                                   spacing3=8)
        self._append_system(
            "Rozmowa AI aktywna w trybie doradczym — bez wykonywania akcji."
            if self.conversation is not None
            and self.conversation.status().provider_connected
            else "Rozmowa lokalna. Aby otrzymać odpowiedzi AI, podłącz bezpieczny model w konfiguracji."
        )

        entry = tk.Frame(self, bg=BG, padx=18)
        entry.pack(fill="x", pady=(0, 7))
        self.input = tk.Text(
            entry, height=3, wrap="word", bg="#252535", fg=INK,
            relief="flat", bd=0, highlightthickness=1,
            highlightbackground="#48435A", highlightcolor=PURPLE,
            insertbackground=INK, font=("Segoe UI", 10),
            padx=12, pady=9,
        )
        self.input.pack(fill="x")
        self.input.bind("<Control-Return>", self._send_shortcut)
        bar = tk.Frame(self, bg=BG, padx=18, pady=9)
        bar.pack(fill="x")
        self.hint = self._label(
            bar, "Ctrl+Enter — wyślij", size=9, color=MUTED,
        )
        self.hint.pack(side="left")
        self.send = tk.Button(
            bar, text="Wyślij wiadomość", command=self._send,
            bg=PURPLE, fg="#151020", activebackground="#C4A8FF",
            font=("Segoe UI Semibold", 10), bd=0, relief="flat",
            padx=18, pady=9, cursor="hand2",
        )
        self.send.pack(side="right")
        self.input.focus_set()

    def _append(self, who, text, tag):
        self.history.configure(state="normal")
        self.history.insert("end", who + "\n", tag)
        self.history.insert("end", text + "\n", "body" if tag != "system" else "notice")
        self.history.configure(state="disabled")
        self.history.see("end")

    def _append_system(self, text):
        self._append("NaviMind · Informacja", text, "system")

    def _refresh(self):
        snapshot = self.inbox.snapshot()
        for message in snapshot.messages:
            if message.message_id <= self.last_id:
                continue
            name, tag = {
                MessageRole.HUMAN: ("Ty", "user"),
                MessageRole.AGENT: ("NaviMind", "agent"),
                MessageRole.SYSTEM: ("System", "system"),
            }[message.role]
            self._append(name, message.text, tag)
            self.last_id = message.message_id

    def _send_shortcut(self, event):
        self._send()
        return "break"

    def _send(self):
        contents = self.input.get("1.0", "end-1c").strip()
        if not contents:
            return
        try:
            message = self.inbox.user_message(contents)
        except (ValueError, RuntimeError) as exc:
            messagebox.showwarning("Wiadomość nieprzyjęta", str(exc), parent=self)
            return
        self.input.delete("1.0", "end")
        self._refresh()
        if self.conversation is not None and self.conversation.submit_current_message(message.message_id):
            self.hint.configure(text="NaviMind przygotowuje odpowiedź…")
        else:
            self._append_system(
                "Instrukcja zapisana. Wykonanie w WindowHub jest wstrzymane. "
                "Brak połączonego modelu rozmownego — możesz pisać dalej."
            )

    def _poll(self):
        if not self.winfo_exists():
            return
        self._refresh()
        self.after(350, self._poll)
