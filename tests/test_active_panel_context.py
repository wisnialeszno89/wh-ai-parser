"""Active UIA panel inference never grants write permission."""
from types import SimpleNamespace as N

from app.agent.runtime.active_panel_context import (
    observe_panel_context, panel_lineage, action_panel_priority, safe_panel_diagnostics,
)
from app.agent.runtime.windowhub_foreground_inspection import (
    inspect_current_windowhub_foreground,
)
from app.agent.runtime.goal_affordance_ranking import order_observed_affordances


def element(label, kind="button", *, selected=None, focused=False, ancestors=()):
    return N(kind=kind, label=label, metadata={
        "source": "windows_ui_automation",
        "uia_visible": True,
        "uia_selected": selected,
        "uia_focused": focused,
        "uia_ancestor_context": ancestors,
    })


def test_selected_tab_is_observed_not_inferred_from_other_panel():
    tab = element("Konstrukcja", "tabitem", selected=True)
    inside = element("Edytuj", ancestors=(
        ("pane", "Layout", "Konstrukcja"),
        ("window", "Window", "Okna"),
    ))
    outside = element("Edytuj", ancestors=(
        ("pane", "Layout", "Szablony wydruków"),
        ("window", "Window", "Okna"),
    ))
    scene = N(elements=(tab, inside, outside))
    context = observe_panel_context(scene)
    assert context.status == "selected_tab_observed"
    assert context.selected_tabs == ("Konstrukcja",)
    assert action_panel_priority(inside, context, goal="edytuj konstrukcję") > action_panel_priority(
        outside, context, goal="edytuj konstrukcję"
    )
    assert "Konstrukcja" in panel_lineage(inside)


def test_focus_is_evidence_but_not_selected_tab():
    scene = N(elements=(element("Pole wysokości", focused=True),))
    context = observe_panel_context(scene)
    assert context.selected_tabs == ()
    assert context.status == "focus_observed_no_unique_selected_tab"
    assert safe_panel_diagnostics(scene)["focused_control_count"] == 1


def test_no_ancestry_is_not_imagined():
    context = observe_panel_context(N(elements=(element("Edytuj"),)))
    assert context.status == "unscoped_controls_only"
    assert context.panel_labels == ()
    assert context.contextual_controls == 0


def test_context_prioritizes_controls_in_active_group():
    active = element("Edytuj", ancestors=(("pane", "x", "Konstrukcja"),))
    inactive = element("Edytuj", ancestors=(("pane", "x", "Szablony wydruków"),))
    tab = element("Konstrukcja", kind="tabitem", selected=True)
    scene = N(elements=(active, inactive, tab))
    context = observe_panel_context(scene)
    class Refs:
        def resolve(self, ref, *, task_id, world_revision):
            return {"old": inactive, "new": active}[ref]
    affordances = [
        {"entity_ref": "old", "description": "click", "name": "click"},
        {"entity_ref": "new", "description": "click", "name": "click"},
    ]
    ranked = order_observed_affordances(
        affordances, goal="edytuj konstrukcję", reference_map=Refs(),
        task_id="t", world_revision=1, panel_context=context,
    )
    assert ranked[0]["entity_ref"] == "new"
    assert len(ranked) == 2


def test_unknown_foreground_title_is_read_only_and_scoped_to_process():
    assert inspect_current_windowhub_foreground(capture=lambda: ("Okna.exe", True))
    assert not inspect_current_windowhub_foreground(capture=lambda: ("Explorer.exe", True))
    assert not inspect_current_windowhub_foreground(capture=lambda: ("Okna.exe", False))


def test_model_context_identifies_generic_area_but_hides_project_names():
    from app.agent.runtime.active_panel_context import panel_model_context
    active = element("Edytuj", ancestors=(
        ("pane", "x", "Szablony wydruków"),
        ("window", "x", "Oferta: Tajna Spółka"),
    ))
    tab = element("Szablony wydruków", kind="tabitem", selected=True)
    scene = N(elements=(active, tab))
    projected = panel_model_context(scene)
    assert projected["selected_areas"] == ["print_templates"]
    assert "print_templates" in projected["visible_area_categories"]
    assert "Tajna" not in repr(projected)
    assert projected["verification"] == "observed_not_authorizing"


def test_unmapped_area_does_not_transmit_any_raw_label():
    from app.agent.runtime.active_panel_context import panel_model_context
    scene = N(elements=(element(
        "Dane umowy klienta ABC",
        kind="tabitem",
        selected=True,
    ),))
    projected = panel_model_context(scene)
    assert projected["selected_areas"] == []
    assert "ABC" not in repr(projected)


def test_unknown_window_recovery_requires_one_visible_unminimized_candidate():
    from app.agent.runtime.windowhub_foreground_inspection import unique_observable_window
    assert unique_observable_window([(52, True, False)]) == 52
    assert unique_observable_window([]) is None
    assert unique_observable_window([(52, True, False), (53, True, False)]) is None
    assert unique_observable_window([(52, True, True)]) is None
    assert unique_observable_window([(52, False, False)]) is None
    assert unique_observable_window([(0, True, False)]) is None
    assert unique_observable_window([(True, True, False)]) is None
