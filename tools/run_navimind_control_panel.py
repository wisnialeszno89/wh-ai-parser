"""NaviMind local control panel — polished compact Tkinter desktop UI.

Run on Windows: python tools/run_navimind_control_panel.py
This is an isolated UI demonstration. It does NOT connect to the running V2
agent, global input hooks or WindowHub. The status always discloses this.
"""
from __future__ import annotations

import tkinter as tk
from tkinter import font as tkfont

from app.agent.runtime.navimind_panel_controller import (
    NaviMindPanelController, PanelMode, PanelSnapshot,
)

BG = "#101019"
CARD = "#1B1B29"
SURFACE = "#252535"
STROKE = "#343348"
FG = "#F5F1FA"
MUTED = "#A6A1B7"
PURPLE = "#A989F9"
PURPLE_DARK = "#48336E"
GOLD = "#E6C789"
RED = "#FF9A9D"
GREEN = "#93D9BE"

POLISH = {
    "takeover": "Przejmij kontrolę",
    "resume": "Wznów pracę",
    "stop": "Zatrzymaj zadanie",
    "training": "Tryb nauki",
}


class RoundedButton(tk.Canvas):
    """Accessible keyboard-clickable rounded action button."""

    def __init__(self, master, *, label, command, width=352, height=55,
                 fill=PURPLE, text_color="#151020", border=None):
        super().__init__(master, width=width, height=height,
                         highlightthickness=0, bd=0, bg=master.cget("bg"),
                         cursor="hand2", takefocus=True)
        self._label, self._command = label, command
        self._fill, self._text_color = fill, text_color
        self._border = border
        self._width, self._height = width, height
        self._draw()
        self.bind("<Button-1>", lambda e: self._invoke())
        self.bind("<Return>", lambda e: self._invoke())
        self.bind("<space>", lambda e: self._invoke())
        self.bind("<FocusIn>", lambda e: self._draw(focused=True))
        self.bind("<FocusOut>", lambda e: self._draw())
        self.bind("<Enter>", lambda e: self._draw(hover=True))
        self.bind("<Leave>", lambda e: self._draw())

    def _draw(self, *, hover=False, focused=False):
        self.delete("all")
        w, h = self._width, self._height
        color = self._fill
        if hover and color == PURPLE:
            color = "#BEA5FF"
        if focused:
            self.create_rectangle(2, 2, w - 2, h - 2, outline=GOLD, width=2)
        r = 16
        # Smooth rounded rectangle using a polygon: no external UI packages.
        coords = [
            r, 5, w-r, 5, w-5, 5+r, w-5, h-r-5,
            w-r, h-5, r, h-5, 5, h-r-5, 5, r+5,
        ]
        self.create_polygon(coords, smooth=True, splinesteps=16,
                            fill=color, outline=self._border or color, width=1)
        self.create_text(w/2, h/2, text=self._label, fill=self._text_color,
                         font=("Segoe UI Semibold", 12))

    def _invoke(self):
        if self._command:
            self._command()

    def set_enabled(self, enabled):
        self._command = self._configured_command if enabled else None
        self.configure(cursor="hand2" if enabled else "arrow")
        if enabled:
            self._fill, self._text_color = self._active_colors
        else:
            self._fill, self._text_color = SURFACE, "#777387"
        self._draw()

    def register_action(self, command):
        self._configured_command = command
        self._active_colors = (self._fill, self._text_color)


class NaviMindPanel(tk.Tk):
    def __init__(self, controller: NaviMindPanelController | None = None):
        super().__init__()
        self.controller = controller or NaviMindPanelController()
        self.host_observation_only = False
        self.title("NaviMind • Centrum sterowania")
        self.geometry("440x675")
        self.minsize(430, 650)
        self.resizable(False, False)
        self.configure(bg=BG)
        self._build()
        self.controller.subscribe(self._update)
        self.protocol("WM_DELETE_WINDOW", self._close)

    def _label(self, parent, text, *, size=10, color=FG, bold=False,
               bg=None, **kwargs):
        return tk.Label(
            parent, text=text, bg=bg or parent.cget("bg"), fg=color,
            font=("Segoe UI Semibold" if bold else "Segoe UI", size),
            anchor="w", **kwargs,
        )

    def _build(self):
        outer = tk.Frame(self, bg=BG, padx=27, pady=22)
        outer.pack(fill="both", expand=True)

        brand = tk.Frame(outer, bg=BG)
        brand.pack(fill="x")
        mark = tk.Canvas(brand, width=39, height=39, bg=BG,
                         highlightthickness=0)
        mark.pack(side="left")
        mark.create_oval(1, 1, 38, 38, fill=PURPLE_DARK, outline=PURPLE, width=1)
        mark.create_text(20, 20, text="N", fill=FG,
                         font=("Segoe UI Semibold", 18))
        names = tk.Frame(brand, bg=BG)
        names.pack(side="left", padx=11)
        self._label(names, "NaviMind", size=17, bold=True).pack(anchor="w")
        self._label(names, "CENTRUM STEROWANIA", size=8,
                    color=MUTED, bold=True).pack(anchor="w")
        self._label(outer, "Twój komputer. Twoje zasady.", size=10,
                    color=MUTED).pack(anchor="w", pady=(18, 19))

        card = tk.Frame(outer, bg=CARD, padx=22, pady=20,
                        highlightbackground=STROKE, highlightthickness=1)
        card.pack(fill="x")
        line = tk.Frame(card, bg=CARD)
        line.pack(fill="x")
        self.dot = tk.Canvas(line, bg=CARD, width=14, height=14,
                             highlightthickness=0)
        self.dot.pack(side="left", padx=(0, 7))
        self.dot.create_oval(3, 3, 12, 12, fill=GOLD, outline="")
        self._label(line, "STATUS AGENTA", size=9, color=MUTED,
                    bold=True).pack(side="left")
        self.connection = self._label(line, "DEMO", size=8, color=GOLD, bold=True)
        self.connection.pack(side="right")
        self.status = self._label(card, "Sterowanie ręczne", size=17, bold=True)
        self.status.pack(anchor="w", pady=(15, 8))
        self.description = self._label(
            card, "Możesz swobodnie korzystać z komputera.",
            size=10, color=MUTED, wraplength=332, justify="left")
        self.description.pack(anchor="w")
        tk.Frame(card, bg=STROKE, height=1).pack(fill="x", pady=(19, 13))
        self._label(card, "AKTUALNE ZADANIE", size=8, color=MUTED,
                    bold=True).pack(anchor="w")
        self.task = self._label(card, "Brak połączonego zadania",
                                size=11, bold=True)
        self.task.pack(anchor="w", pady=(4, 0))

        self._label(outer, "STEROWANIE", size=9, color=MUTED,
                    bold=True).pack(anchor="w", pady=(24, 10))

        buttons = tk.Frame(outer, bg=BG)
        buttons.pack(fill="x")
        self.primary = RoundedButton(
            buttons, label="Przejmij kontrolę", command=self.controller.takeover,
            width=380, fill=PURPLE,
        )
        self.primary.pack(pady=(0, 10))
        self.primary.register_action(self.controller.takeover)
        self.secondary = RoundedButton(
            buttons, label="Wznów pracę", command=self.controller.resume,
            width=380, height=50, fill=SURFACE, text_color=FG, border=STROKE,
        )
        self.secondary.pack()
        self.secondary.register_action(self.controller.resume)

        action_row = tk.Frame(outer, bg=BG)
        action_row.pack(fill="x", pady=(16, 0))
        self.training_btn = tk.Button(
            action_row, text="✦  Tryb nauki", command=self.controller.training,
            bg=BG, fg=PURPLE, activebackground=BG,
            activeforeground=FG, font=("Segoe UI Semibold", 10),
            relief="flat", bd=0, cursor="hand2", padx=0, pady=8,
        )
        self.training_btn.pack(side="left")
        self.stop_btn = tk.Button(
            action_row, text="■  Zatrzymaj zadanie", command=self._stop,
            bg=BG, fg=RED, activebackground=BG,
            activeforeground="#FFC4C5", font=("Segoe UI Semibold", 10),
            relief="flat", bd=0, cursor="hand2", padx=0, pady=8,
        )
        self.stop_btn.pack(side="right")

        tk.Frame(outer, height=1, bg=STROKE).pack(fill="x", pady=(15, 13))
        self.notice = self._label(
            outer, "TRYB DEMONSTRACYJNY • Brak połączenia z WindowHub",
            size=9, color=GOLD, wraplength=380, justify="left",
        )
        self.notice.pack(anchor="w")
        self._label(
            outer, "Wznowienie wymaga sprawdzenia aktualnego dokumentu.",
            size=9, color=MUTED, wraplength=380,
        ).pack(anchor="w", pady=(6, 0))

    def _update(self, state: PanelSnapshot):
        self.status.configure(text=state.title)
        self.description.configure(text=state.detail)
        self.task.configure(text=state.document_label)
        dot_color = {
            PanelMode.HUMAN: GOLD,
            PanelMode.RESUME_PENDING: GOLD,
            PanelMode.AGENT_READY: GREEN,
            PanelMode.LEARNING: PURPLE,
            PanelMode.STOPPED: RED,
        }[state.mode]
        self.dot.itemconfigure(1, fill=dot_color)
        read_only = self.host_observation_only
        self.connection.configure(
            text="OBSERWACJA" if read_only else ("HOST" if state.connected else "DEMO")
        )
        if read_only:
            self.notice.configure(
                text="HOST OBSERWACYJNY • Nie uruchamia działań WindowHub",
                fg=GOLD,
            )
            if state.mode == PanelMode.AGENT_READY:
                self.status.configure(text="Oferta rozpoznana")
                self.description.configure(
                    text="Potwierdzono aktualny dokument. Sterowanie AI nadal wyłączone."
                )
        else:
            self.notice.configure(
                text=("POŁĄCZONY HOST • kontrola aktualnego dokumentu obowiązkowa"
                      if state.connected else
                      "TRYB DEMONSTRACYJNY • Brak połączenia z WindowHub"),
                fg=GREEN if state.connected else GOLD,
            )
        self.primary.set_enabled(state.can_takeover)
        self.secondary.set_enabled(state.can_resume)
        self.training_btn.configure(
            state="normal" if state.can_learn else "disabled"
        )
        self.stop_btn.configure(
            state="normal" if state.can_stop else "disabled"
        )

    def _stop(self):
        # Stop is intentionally final for this task. To avoid accidental
        # dismissal we require confirmation but never auto-save anything.
        from tkinter.messagebox import askyesno
        if askyesno("Zatrzymać zadanie?",
                    "Zatrzymać bieżące zadanie NaviMind? Stary plan nie będzie wznowiony.",
                    parent=self):
            self.controller.stop()

    def _close(self):
        # Closing the UI must NOT silently release the computer to the agent.
        self.controller.takeover()
        self.destroy()


def main() -> int:
    try:
        app = NaviMindPanel()
    except tk.TclError as exc:
        print("NAVIMIND_PANEL_DISPLAY_UNAVAILABLE=" + type(exc).__name__)
        return 2
    app.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
