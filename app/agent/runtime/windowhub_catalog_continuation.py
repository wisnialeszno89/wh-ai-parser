"""Catalog-aware, bounded continuation after verified WindowHub dimensions.

Never selects a merely similar color or glazing option. Every transition is
followed by fresh UIA readback. The module does not save or finalize a draft.
"""
from __future__ import annotations

from app.agent.learning.windowhub_demonstration import stage_of

COLOR_COMBINATIONS = {
    ("antracyt", "biały"): (
        "Antracyt / Biały",
        "Antracyt / Bialy",
        "Antracyt zewnętrzny / Biały wewnętrzny",
        "Antracyt zew. / Biały wew.",
        "RAL 7016 / Biały",
        "RAL 7016 / Bialy",
    ),
}
GLAZING_LABELS = {
    2: (
        "2glass",
        "2 szyby",
        "Pakiet dwuszybowy",
        "Dwuszybowy",
        "2-szybowy",
    ),
    3: (
        "3glass",
        "3 szyby",
        "Pakiet trzyszybowy",
        "Trzyszybowy",
        "3-szybowy",
    ),
}


def catalog_options_for(*, outside: str, inside: str, glazing_panes: int):
    from app.agent.learning.windowhub_catalog_memory import read_skill, skill_key
    color_field, color_key = skill_key(outside=outside, inside=inside)
    glazing_field, glazing_key = skill_key(glazing_panes=glazing_panes)
    colors = COLOR_COMBINATIONS.get((outside.casefold().strip(), inside.casefold().strip()), ())
    glazing = GLAZING_LABELS.get(glazing_panes, ())
    learned_color = read_skill(color_field, color_key)
    learned_glazing = read_skill(glazing_field, glazing_key)
    # Previously taught exact catalog values take priority over generic
    # synonyms: otherwise multiple whitelist hits might become ambiguous.
    if learned_color:
        colors = (learned_color,)
    if learned_glazing:
        glazing = (learned_glazing,)
    return colors, glazing


def exact_selected(scene, field_name: str, choices: tuple[str, ...]) -> bool:
    from app.agent.offers.windowhub_offer_form_map import WindowHubOfferFormMap
    snapshot = WindowHubOfferFormMap().inspect(scene)
    candidate = snapshot.field(field_name) if snapshot else None
    value = (
        (candidate.element.metadata or {}).get("current_value")
        if candidate is not None and candidate.is_unique and candidate.element is not None
        else None
    )
    return isinstance(value, str) and value.strip().casefold() in {
        name.strip().casefold() for name in choices
    }


def dimensions_match(scene, *, width: int, height: int) -> bool:
    from app.agent.offers.windowhub_offer_form_map import WindowHubOfferFormMap
    snapshot = WindowHubOfferFormMap().inspect(scene)
    if snapshot is None:
        return False
    for name, desired in (("width_1", width), ("height_1", height)):
        match = snapshot.field(name)
        if match is None or not match.is_unique or match.element is None:
            return False
        value = (match.element.metadata or {}).get("current_value")
        if not isinstance(value, str) or value.strip() != str(desired):
            return False
    return True


def continue_to_construction(loop, *, width: int, height: int,
                             color_outside: str, color_inside: str,
                             glazing_panes: int, interactive_handoff: bool = False, ask=input) -> int:
    from tools.run_windowhub_top_trans_single_window_mission import (
        inspect, observe_step, advance_known_wizard, select_catalog_option_once,
    )
    colors, glazing = catalog_options_for(
        outside=color_outside, inside=color_inside, glazing_panes=glazing_panes,
    )
    scene = inspect(loop)
    stage = stage_of(scene)
    print("CATALOG_ENTRY_STAGE=" + str(stage))
    if stage == "dimensions":
        if not dimensions_match(scene, width=width, height=height):
            print("STOP: Requested dimensions were not proven in current wizard.")
            return 6
        if not advance_known_wizard(scene, expected_stage="basic_parameters"):
            print("STOP: Next from dimensions was not uniquely verified.")
            return 6
        scene = observe_step(loop, "basic_parameters")
        if scene is None:
            print("STOP: Basic parameters stage not observed.")
            return 6
        stage = "basic_parameters"

    if stage == "basic_parameters":
        if not colors:
            print("STOP: No exact approved two-sided color mapping.")
            return 4
        if not exact_selected(scene, "profile_color", colors):
            selected = bool(colors) and select_catalog_option_once(
                scene, field_name="profile_color", approved_options=colors,
            )
            if selected:
                scene = inspect(loop)
                if not exact_selected(scene, "profile_color", colors):
                    print("STOP: Selected color could not be read back.")
                    return 6
            else:
                if not interactive_handoff:
                    print("STOP: Exact two-sided color unavailable.")
                    return 4
                from app.agent.learning.windowhub_catalog_memory import skill_key
                from app.agent.runtime.windowhub_catalog_handoff import teach_and_resume
                field, key = skill_key(outside=color_outside, inside=color_inside)
                scene = teach_and_resume(
                    loop, field=field, key=key, stage="basic_parameters",
                    meaning=f"zewnątrz {color_outside}, wewnątrz {color_inside}",
                    ask=ask,
                )
                if scene is None:
                    print("STOP: Color teach/resume not verified.")
                    return 4
        print("PROFILE_COLOR_BOTH_SIDES_VERIFIED=True")
        if not advance_known_wizard(scene, expected_stage="glazing"):
            print("STOP: Glazing wizard entry unavailable.")
            return 6
        scene = observe_step(loop, "glazing")
        if scene is None:
            print("STOP: Glazing stage not verified.")
            return 6
        stage = "glazing"

    if stage == "glazing":
        if not glazing:
            print("STOP: Unsupported glazing pane count.")
            return 4
        if not exact_selected(scene, "glazing_package", glazing):
            selected = bool(glazing) and select_catalog_option_once(
                scene, field_name="glazing_package", approved_options=glazing,
            )
            if selected:
                scene = inspect(loop)
                if not exact_selected(scene, "glazing_package", glazing):
                    print("STOP: Glazing could not be read back.")
                    return 6
            else:
                if not interactive_handoff:
                    print("STOP: Exact glazing option unavailable.")
                    return 4
                from app.agent.learning.windowhub_catalog_memory import skill_key
                from app.agent.runtime.windowhub_catalog_handoff import teach_and_resume
                field, key = skill_key(glazing_panes=glazing_panes)
                scene = teach_and_resume(
                    loop, field=field, key=key, stage="glazing",
                    meaning=f"pakiet {glazing_panes}-szybowy", ask=ask,
                )
                if scene is None:
                    print("STOP: Glazing teach/resume not verified.")
                    return 4
        print("GLAZING_PACKAGE_VERIFIED=True")
        if not advance_known_wizard(scene, expected_stage="hardware"):
            print("STOP: Hardware wizard entry unavailable.")
            return 6
        scene = observe_step(loop, "hardware")
        if scene is None:
            print("STOP: Hardware stage not verified.")
            return 6
        stage = "hardware"

    if stage == "hardware":
        print("WIZARD_STAGE_REACHED=hardware")
        print("MODIFIER_REACHED=False")
        # Hardware and opening direction are catalog-dependent. We cannot
        # safely assume that Finish creates a valid configured sash.
        if not interactive_handoff:
            print("STOP: Hardware configuration needs a verified skill.")
            return 4
        print("TEACH_MODE=hardware_to_modifier")
        try:
            ready = ask(
                "Skonfiguruj okucia i przejdź ręcznie do edytora budowy okna; "
                "potem wpisz 'gotowe' (inne = przerwij): "
            )
        except (EOFError, KeyboardInterrupt):
            return 4
        if ready.strip().casefold() != "gotowe":
            return 4
        from app.agent.runtime.windowhub_window_activation import activate_windowhub_workflow_window
        focused, info = activate_windowhub_workflow_window()
        print("HARDWARE_TEACH_REFOCUS=" + info)
        if not focused:
            return 4
        fresh = inspect(loop)
        if stage_of(fresh) != "modifier":
            print("STOP: Construction editor not observed after teaching.")
            return 4
        try:
            consent = ask("Kontynuować pracę w edytorze od tego miejsca? [tak/N]: ")
        except (EOFError, KeyboardInterrupt):
            return 4
        if consent.strip().casefold() not in {"tak", "t"}:
            return 4
        focused, info = activate_windowhub_workflow_window()
        print("HARDWARE_RESUME_REFOCUS=" + info)
        if not focused or stage_of(inspect(loop)) != "modifier":
            print("HARDWARE_RESUME_STAGE_LOST=True")
            return 4
        # The observed transition can be recorded by the existing teach
        # recorder, but is not yet treated as proof of a specific button.
        print("HARDWARE_HANDOFF_VERIFIED=modifier")
        print("MODIFIER_REACHED=True")
        return 0

    if stage == "modifier":
        print("MODIFIER_REACHED=True")
        print("DRAFT_SAVED_VERIFIED=False")
        return 0

    print("STOP: Unsupported catalog stage " + str(stage))
    return 4
