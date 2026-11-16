"""Explicit WindowHub catalog demonstration, exact-value readback, resumption."""
from __future__ import annotations

from app.agent.learning.windowhub_demonstration import stage_of
from app.agent.offers.windowhub_offer_form_map import WindowHubOfferFormMap
from app.agent.learning.windowhub_catalog_memory import record_skill


def current_catalog_value(scene, field_name):
    snapshot = WindowHubOfferFormMap().inspect(scene)
    field = snapshot.field(field_name) if snapshot is not None else None
    if field is None or not field.is_unique or field.element is None:
        return None
    value = (field.element.metadata or {}).get("current_value")
    return value.strip() if isinstance(value, str) and value.strip() else None


def teach_and_resume(loop, *, field, key, stage, meaning, ask=input):
    from tools.run_windowhub_top_trans_single_window_mission import inspect
    print("TEACH_MODE=available")
    print("TEACH_INSTRUCTION=Choose the exact required catalog option manually.")
    try:
        ready = ask("Wybierz opcję w WindowHub, potem wpisz 'gotowe': ")
    except (EOFError, KeyboardInterrupt):
        return None
    if ready.strip().casefold() != "gotowe":
        return None
    scene = inspect(loop)
    if stage_of(scene) != stage:
        print("TEACH_ERROR=unexpected_stage")
        return None
    value = current_catalog_value(scene, field)
    if value is None:
        print("TEACH_ERROR=no_native_catalog_readback")
        return None
    print("TEACH_OBSERVED_LABEL=" + repr(value))
    try:
        approved = ask(f"Czy '{value}' odpowiada konfiguracji '{meaning}'? [tak/N]: ")
        if approved.strip().casefold() not in ("tak", "t"):
            return None
        save = ask("Zapisać tę sprawdzoną umiejętność? [tak/N]: ")
        if save.strip().casefold() in ("tak", "t"):
            print("TEACH_SAVED=" + str(record_skill(
                field, key, value, human_confirmed=True, readback_verified=True
            )))
        resume = ask("Kontynuować pracę z tego miejsca według wytycznych? [tak/N]: ")
    except (EOFError, KeyboardInterrupt):
        return None
    if resume.strip().casefold() not in ("tak", "t"):
        print("TEACH_RESUME_DECLINED=True")
        return None
    fresh = inspect(loop)
    if stage_of(fresh) != stage or current_catalog_value(fresh, field) != value:
        print("TEACH_RESUME_REVALIDATION_FAILED=True")
        return None
    print("TEACH_RESUME_APPROVED=True")
    return fresh
