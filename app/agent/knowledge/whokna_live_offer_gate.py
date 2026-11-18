"""Read-only live offer readiness gate for a manually prepared WindowHub screen.

A successful gate means a safe scene was observed, NOT that any offer
stage was completed. No mouse/keyboard control is used here.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Gate:
    ok: bool
    reason: str
    scene_stage: str
    title: str


def check_offer_scene(
    *,
    process: str,
    title: str,
    has_window_rect: bool,
    has_image: bool,
    observed_elements: int,
) -> Gate:
    name = (process or "").replace("\\", "/").rsplit("/", 1)[-1].casefold()
    title = (title or "").strip()
    low = title.casefold()
    if name != "okna.exe":
        return Gate(False, "foreground_not_windowhub", "unknown", title)
    if "zlc/" in low or "zamówienie" in low or "zamowienie" in low:
        return Gate(False, "business_order_forbidden", "order", title)
    if not has_window_rect or not has_image:
        return Gate(False, "screen_observation_incomplete", "unknown", title)
    if observed_elements < 1:
        return Gate(False, "no_scene_elements", "unknown", title)
    if low.startswith("okna - ofr/"):
        return Gate(True, "test_offer_visible", "offer_document", title)
    if low.startswith("okna - start1"):
        return Gate(True, "start_workspace_visible", "start", title)
    if low in {"dodawanie nowej pozycji", "wielkość okna",
               "wielkosc okna", "właściwości dokumentu",
               "wlasciwosci dokumentu"}:
        return Gate(True, "offer_wizard_visible", "wizard", title)
    return Gate(False, "unrecognized_windowhub_stage", "unknown", title)


def observe_offer_gate(loop: Any) -> tuple[Gate, Any]:
    scene = loop.observe_scene()
    obs = scene.observation
    meta = obs.metadata
    shot = meta.get("screenshot")
    gate = check_offer_scene(
        process=obs.state.active_application or "",
        title=obs.state.active_window_title or "",
        has_window_rect=meta.get("window_rect") is not None,
        has_image=getattr(shot, "image", None) is not None,
        observed_elements=len(scene.elements),
    )
    return gate, scene
