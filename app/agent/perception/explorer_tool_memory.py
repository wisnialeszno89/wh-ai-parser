"""Passive Explorer memory: avoid rediscovering reliable hover descriptions.

This is screen-local, unverified perceptual memory, NOT a reusable execution
skill. Coordinates are not valid across different window layouts.
"""
from __future__ import annotations

import json
from pathlib import Path


def same_place(one, two, radius: int = 26) -> bool:
    if not isinstance(one, (list, tuple)) or not isinstance(two, (list, tuple)):
        return False
    if len(one) != 2 or len(two) != 2:
        return False
    try:
        return abs(int(one[0]) - int(two[0])) <= radius and abs(
            int(one[1]) - int(two[1])
        ) <= radius
    except (ValueError, TypeError):
        return False


def load_memory(path: Path, *, application: str, window_title: str,
                window_size: tuple[int, int]) -> list[dict]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return []
    if data.get("schema") != "navimind.icon_map.unverified.v1":
        return []
    if data.get("application", "").casefold() != application.casefold():
        return []
    # Old maps have no title/size. Trust them as exploratory hints only on
    # the first migration; never grant action authorization based on memory.
    title = data.get("window_title")
    if title is not None and title != window_title:
        return []
    size = data.get("window_size")
    if size is not None and list(size) != list(window_size):
        return []
    return [entry for entry in data.get("icons", [])
            if isinstance(entry, dict)]


def known_tool(entry: dict) -> bool:
    return (entry.get("evidence") == "ocr_candidate_unverified"
            and isinstance(entry.get("label_hypothesis"), str)
            and len(entry["label_hypothesis"].strip()) >= 5
            and float(entry.get("ocr_confidence") or 0) >= 40)


def select_for_learning(candidates: list, learned: list[dict], *, limit: int):
    """Prioritize never-observed coordinates, retry uncertain tooltips later."""
    new, uncertain, already = [], [], []
    for item in candidates:
        pointer = [item.x + item.width // 2, item.y + item.height // 2]
        matching = [entry for entry in learned
                    if same_place(entry.get("pointer"), pointer)]
        if any(known_tool(entry) for entry in matching):
            already.append(item)
        elif matching:
            uncertain.append(item)
        else:
            new.append(item)
    return (new + uncertain)[:limit], {
        "new": len(new), "retry_uncertain": len(uncertain),
        "known_skipped": len(already),
    }


def merge_observations(learned: list[dict], records: list[dict]) -> list[dict]:
    """Latest readable OCR evidence wins. Unreadable repeat never erases it."""
    merged = list(learned)
    for record in records:
        info = record.get("tooltip_ocr") or {}
        point = record.get("hover_at_relative")
        if not isinstance(point, (list, tuple)):
            continue
        new_entry = {
            "relative_bounds": record.get("rect_relative"),
            "pointer": list(point),
            "label_hypothesis": info.get("text"),
            "ocr_confidence": info.get("confidence"),
            "evidence": info.get("status"),
            "behavior_verified": False,
        }
        index = next((i for i, entry in enumerate(merged)
                      if same_place(entry.get("pointer"), point)), None)
        if index is None:
            merged.append(new_entry)
        elif known_tool(new_entry) or not known_tool(merged[index]):
            merged[index] = new_entry
    return merged
