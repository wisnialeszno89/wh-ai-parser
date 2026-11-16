"""Verify a WindowHub stage transition from a fresh scene and actual input.

A control-loop postcondition may be evaluated before a MDI tab finishes
updating. An independently observed stage can resolve only this bounded
navigation ambiguity; input must have actually executed.
"""
from __future__ import annotations

from app.agent.learning.windowhub_demonstration import stage_of


def input_was_executed(result) -> bool:
    execution_loop = getattr(result, "last_execution_result", None)
    attempt = getattr(execution_loop, "last_attempt", None)
    execution = getattr(attempt, "execution_result", None)
    return (getattr(execution, "metadata", None) or {}).get("executed") is True


def verified_navigation_transition(result, scene, *, expected_stage: str) -> bool:
    if expected_stage not in {"start", "document_properties"}:
        raise ValueError("unsupported_navigation_stage")
    if not input_was_executed(result):
        return False
    if stage_of(scene) != expected_stage:
        return False
    if expected_stage == "start":
        tabs = [
            element for element in scene.elements
            if element.kind == "tabitem"
            and (element.label or "").strip().casefold() == "start1"
            and (element.metadata or {}).get("source") in {
                "windows_ui_automation", "windowhub_ui_automation",
            }
            and (element.metadata or {}).get("uia_visible") is True
        ]
        return len(tabs) == 1 and (tabs[0].metadata or {}).get("uia_selected") is True
    return True
