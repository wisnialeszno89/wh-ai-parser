from __future__ import annotations

from copy import deepcopy


COMPUTER_FOUNDATION_VERSION = "1"


COMPUTER_FOUNDATION_KNOWLEDGE: dict[str, object] = {
    "name": "Computer Foundation",
    "version": COMPUTER_FOUNDATION_VERSION,
    "purpose": (
        "General semantic knowledge for operating graphical computer "
        "interfaces. Use this knowledge to interpret common UI controls "
        "and choose safe semantic actions. The observed world remains "
        "authoritative for what is actually present."
    ),
    "ui_model": {
        "window": (
            "A top-level application surface. It contains documents, "
            "panels, dialogs and controls."
        ),
        "dialog": (
            "A temporary interaction surface that may require completion "
            "or cancellation before the underlying window can be used."
        ),
        "button": (
            "A visible control that normally triggers an action when "
            "activated."
        ),
        "tabitem": (
            "A selectable navigation control that switches the visible "
            "section or context of a window."
        ),
        "edit": (
            "A text-entry field. It normally accepts or changes a textual "
            "value."
        ),
        "checkbox": (
            "A toggle control representing an on/off or yes/no state."
        ),
        "combobox": (
            "A control that exposes a value and normally allows choosing "
            "from available options."
        ),
        "listitem": (
            "An item inside a list that can normally be selected."
        ),
        "menuitem": (
            "An item in a menu that normally triggers a command or opens "
            "another menu."
        ),
        "radiobutton": (
            "A mutually exclusive choice within a group."
        ),
        "treeitem": (
            "A selectable item in a hierarchical tree."
        ),
        "hyperlink": (
            "A visible link that normally opens or navigates to a target."
        ),
        "icon": (
            "An icon is not automatically actionable. If an actionable "
            "icon is exposed semantically as a button or another control, "
            "use the observed semantic label and role."
        ),
    },
    "common_interactions": {
        "click": (
            "Activate a visible semantic control such as a button, tab, "
            "menu item or selectable item."
        ),
        "write_text": (
            "Enter a requested value into a visible editable field."
        ),
        "select": (
            "Choose a visible option or selectable control when the world "
            "exposes it semantically."
        ),
        "navigate": (
            "Use visible navigation controls to move to another section "
            "or context."
        ),
    },
    "form_rules": (
        "Labels describe the meaning of nearby fields and controls.",
        "A field should be identified by semantic evidence such as its "
        "label, role and UI structure.",
        "Do not infer a field only from its ordinal position when multiple "
        "fields are plausible.",
        "Before writing, check whether the requested value is already "
        "present.",
        "After writing or selecting a value, re-observe the resulting state "
        "before continuing.",
    ),
    "navigation_rules": (
        "A selected tab normally represents the currently visible section.",
        "A tab should be interpreted in the context of its containing "
        "document or window.",
        "A dialog may temporarily own interaction while it is open.",
        "A menu item normally changes state or opens a new visible context.",
        "Do not assume navigation succeeded merely because an action was "
        "attempted.",
    ),
    "verification_rules": (
        "Every state-changing action should have observable evidence of "
        "the expected result.",
        "For a click, prefer evidence such as changed selection, a new "
        "visible section, an opened dialog or another semantic state change.",
        "For text entry, verify the field value after the mutation.",
        "When the expected state change cannot be observed safely, stop "
        "rather than claiming success.",
    ),
    "ambiguity_rules": (
        "Human-readable labels can appear more than once.",
        "Resolve duplicate labels using semantic role, UI hierarchy, "
        "active document, dialog ownership and other observed context.",
        "Do not resolve ambiguity using screen coordinates.",
        "Do not invent runtime ids, automation ids, window handles or "
        "tracked object ids as model targets.",
        "The current observed world is the source of truth for what exists "
        "on screen right now.",
    ),
    "execution_boundary": (
        "Knowledge describes meaning and expected behavior. It does not "
        "authorize low-level execution or bypass local safety checks."
    ),
}


def get_computer_foundation_knowledge() -> dict[str, object]:
    """Return an isolated copy of the built-in computer knowledge."""
    return deepcopy(COMPUTER_FOUNDATION_KNOWLEDGE)


def build_local_knowledge(
    application_knowledge: dict[str, object] | None,
) -> dict[str, object]:
    """Combine built-in computer knowledge with application knowledge."""
    local = dict(application_knowledge or {})
    local.setdefault(
        "computer_foundation",
        get_computer_foundation_knowledge(),
    )
    return local
