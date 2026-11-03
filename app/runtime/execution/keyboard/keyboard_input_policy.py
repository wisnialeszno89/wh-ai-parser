"""Allowlisted keyboard navigation sequences for controlled computer use.

Only navigation keys and app/tab switching are exposed. Destructive/system
shortcuts (for example Alt+F4, Ctrl+Alt+Delete, Win+L, Delete and Enter) are
deliberately excluded until a separate confirmation policy exists.
"""

from __future__ import annotations


KEY_SEQUENCE_MAP: dict[str, tuple[str, ...]] = {
    "tab": ("tab",),
    "shift+tab": ("shift", "tab"),
    "escape": ("esc",),
    "alt+tab": ("alt", "tab"),
    "ctrl+tab": ("ctrl", "tab"),
    "ctrl+shift+tab": ("ctrl", "shift", "tab"),
    "pageup": ("pageup",),
    "pagedown": ("pagedown",),
    "up": ("up",),
    "down": ("down",),
    "left": ("left",),
    "right": ("right",),
    "home": ("home",),
    "end": ("end",),
}

SAFE_KEY_SEQUENCES = tuple(KEY_SEQUENCE_MAP)


def normalize_keyboard_sequence(value: object) -> tuple[str, ...]:
    """Return a normalized allowlisted sequence or fail closed."""
    if not isinstance(value, str) or not value.strip() or len(value) > 32:
        raise ValueError("keyboard_sequence_invalid")

    normalized = "+".join(
        part.strip().casefold()
        for part in value.split("+")
    )
    if not normalized or any(not part for part in normalized.split("+")):
        raise ValueError("keyboard_sequence_invalid")

    try:
        return KEY_SEQUENCE_MAP[normalized]
    except KeyError as exc:
        raise ValueError("keyboard_sequence_not_allowed") from exc
