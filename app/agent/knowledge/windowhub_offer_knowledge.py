from __future__ import annotations


WINDOWHUB_OFFER_KNOWLEDGE: dict[str, object] = {
    "application": "WindowHub",
    "purpose": (
        "Guide safe semantic navigation of the WindowHub quotation workflow. "
        "The model must use the current visible scene as the source of truth "
        "for actual controls."
    ),
    "workflow": (
        {
            "stage": 1,
            "name": "start_new_offer",
            "goal": "Start a new quotation.",
            "expected_visible_controls": ("Start1", "Nowa oferta"),
            "preferred_action_sequence": (
                "Before clicking Nowa oferta, compare the control's explicit document_scope with the active document.",
                "If Nowa oferta is explicitly scoped to another document and the unique Start1 document tab is visible but unselected, click Start1 first and re-observe the scene.",
                "Resolve Nowa oferta again after the tab switch; click it only when its scope is valid for the current scene.",
                "Do not switch to or modify an existing OFR offer tab just to reach Nowa oferta.",
            ),
            "typical_next_action": "click_screen_element",
        },
        {
            "stage": 2,
            "name": "customer_and_preferences",
            "goal": (
                "Complete the new-offer dialog with customer and valuation "
                "preferences, then confirm it."
            ),
            "expected_visible_controls": ("OK", "Anuluj"),
            "preferred_action_sequence": (
                "write required customer/preferences fields",
                "click OK",
            ),
        },
        {
            "stage": 3,
            "name": "position_type",
            "goal": "Add the quotation position and choose a window.",
            "expected_semantic_targets": (
                "Dodaj artykuł do konstrukcji",
                "okno",
                "OK",
            ),
            "preferred_action_sequence": (
                "open position/item selector",
                "choose visible window product",
                "click OK",
            ),
        },
        {
            "stage": 4,
            "name": "dimensions",
            "goal": "Enter the requested width and height.",
            "field_roles": (
                "width",
                "height",
            ),
            "preferred_action_sequence": (
                "write width",
                "write height",
                "click OK",
            ),
        },
        {
            "stage": 5,
            "name": "basic_window_parameters",
            "goal": "Set basic window parameters such as colour.",
            "field_roles": (
                "colour",
                "glazing",
                "opening",
            ),
            "preferred_action_sequence": (
                "write/select requested values",
                "click Zakończ",
            ),
        },
        {
            "stage": 6,
            "name": "construction_editor",
            "goal": (
                "Work with the actual construction editor only after the "
                "basic parameter stage has been completed."
            ),
            "preferred_action_sequence": (
                "observe construction-specific controls",
                "choose only controls supported by the visible scene",
                "verify after each mutation",
            ),
        },
    ),
    "field_synonyms": {
        "product_type": (
            "rodzaj produktu",
            "typ produktu",
            "produkt",
            "product type",
            "okno",
            "okna",
            "window",
            "windows",
            "drzwi",
            "door",
            "drzwi balkonowe",
            "balcony door",
            "przesuwne",
            "sliding door",
            "hs",
        ),
        "customer": (
            "klient",
            "kontrahent",
            "odbiorca",
            "nabywca",
        ),
        "width": (
            "szerokość",
            "szer",
            "width",
        ),
        "height": (
            "wysokość",
            "wys",
            "height",
        ),
        "quantity": (
            "ilość",
            "liczba",
            "sztuk",
            "sztuki",
        ),
        "colour": (
            "kolor",
            "barwa",
            "RAL",
        ),
        "glazing": (
            "szyba",
            "szklenie",
            "pakiet szybowy",
        ),
        "opening": (
            "otwarcie",
            "otwieranie",
            "skrzydło",
            "FIX",
        ),
    },
    "interface_guide": {
        "version": "1",
        "scope": (
            "Semantic guide built from accessible control names observed in WindowHub "
            "and the existing offer workflow. These entries explain labels and "
            "intended use; they do not prove that an action has succeeded."
        ),
        "controls": (
            {
                "label": "Start1",
                "role": "document tab",
                "meaning": (
                    "A document/workspace tab used by the new-offer navigation guard "
                    "when Nowa oferta is scoped to a different document."
                ),
                "use_when": (
                    "It is the unique visible, enabled, unselected document tab and "
                    "the current scene confirms the cross-document navigation condition."
                ),
                "after_action": "Re-observe the scene and resolve Nowa oferta again.",
                "risk": "navigation",
                "evidence": "UIA label observed; routing rule covered by unit tests; live tab switch not yet verified",
            },
            {
                "label": "NOWA OFERTA",
                "aliases": ("Nowa oferta",),
                "role": "button",
                "meaning": "Begin the new quotation workflow.",
                "use_when": "The user explicitly requests a new offer and the button is valid for the active document.",
                "avoid_when": "Continuing an existing offer, or when its explicit document scope conflicts with the active document.",
                "after_action": "Re-observe and identify the next visible dialog or workflow stage.",
                "risk": "starts a new workflow",
                "evidence": "UIA label observed; intent inferred from label and existing workflow guidance; live form-open not yet verified",
            },
            {
                "label": "ISTNIEJĄCE DOKUMENTY",
                "role": "button",
                "meaning": "Browse or open existing documents.",
                "use_when": "Only when the user explicitly asks to find or open an existing document.",
                "avoid_when": "Starting a new offer.",
                "risk": "existing-document navigation",
                "evidence": "UIA label observed; meaning inferred from label",
            },
            {
                "label": "NOWE ZLECENIE",
                "role": "button",
                "meaning": "Start a new production/work order, not a quotation.",
                "avoid_when": "The requested task is to prepare a new quotation.",
                "risk": "starts a different workflow",
                "evidence": "UIA label observed; meaning inferred from label",
            },
            {
                "label": "NOWE ZAMÓWIENIE",
                "role": "button",
                "meaning": "Start a new order workflow.",
                "avoid_when": "The requested task is to prepare a new quotation.",
                "risk": "starts a different workflow",
                "evidence": "UIA label observed; meaning inferred from label",
            },
            {
                "label": "ZAMÓWIENIE ZBIORCZE",
                "role": "button",
                "meaning": "Open the bulk/combined order workflow.",
                "avoid_when": "The requested task is a single new quotation.",
                "risk": "starts a different workflow",
                "evidence": "UIA label observed; meaning inferred from label",
            },
            {
                "label": "NOWA OPTYMALIZACJA",
                "role": "button",
                "meaning": "Start an optimization workflow.",
                "avoid_when": "The requested task is to prepare a new quotation.",
                "risk": "starts a different workflow",
                "evidence": "UIA label observed; meaning inferred from label",
            },
            {
                "label": "WYSLIJ LUB ODBIERZ ZLECENIE",
                "aliases": ("WYŚLIJ LUB ODBIERZ ZLECENIE",),
                "role": "button",
                "meaning": "Open the send/receive work-order workflow.",
                "avoid_when": "Creating a new quotation.",
                "risk": "external or operational workflow; never choose incidentally",
                "evidence": "UIA label observed; meaning inferred from label",
            },
            {
                "label": "MAGAZYN",
                "role": "button",
                "meaning": "Open the inventory/warehouse area.",
                "avoid_when": "Creating a new quotation unless explicitly required by the user.",
                "risk": "navigate to another module",
                "evidence": "UIA label observed; meaning inferred from label",
            },
            {
                "label": "CENTRUM INFORMACJI",
                "role": "button",
                "meaning": "Open the information/help area.",
                "avoid_when": "Not a step in the standard new-offer workflow.",
                "risk": "navigation",
                "evidence": "UIA label observed; meaning inferred from label",
            },
            {
                "label": "Dodaj artykuł do konstrukcji",
                "role": "button",
                "meaning": "Add an item to the current construction.",
                "use_when": "Only after the new-offer flow reaches a construction/position stage.",
                "risk": "modifies offer contents",
                "evidence": "UIA label observed; consistent with existing offer workflow guidance",
            },
            {
                "label": "Dodaj artykuł do dodatków",
                "role": "button",
                "meaning": "Add an item to the current accessories/add-ons area.",
                "use_when": "Only when the user requested an accessory and the current stage supports it.",
                "risk": "modifies offer contents",
                "evidence": "UIA label observed; meaning inferred from label",
            },
            {
                "label": "Kalkuluj pozycję",
                "role": "button",
                "meaning": "Calculate the current offer position.",
                "use_when": "Only when calculation of the current position is the intended next stage.",
                "risk": "calculation",
                "evidence": "UIA label observed; meaning inferred from label",
            },
            {
                "label": "Kalkuluj ofertę",
                "role": "button",
                "meaning": "Calculate the quotation.",
                "use_when": "Only when the user workflow has reached quotation calculation.",
                "risk": "calculation",
                "evidence": "UIA label observed; meaning inferred from label",
            },
            {
                "label": "Podsumowanie z fakturą",
                "role": "button",
                "meaning": "Open or produce the summary/invoice-related view.",
                "avoid_when": "The task is only to create an initial offer draft.",
                "risk": "document/financial workflow",
                "evidence": "UIA label observed; meaning inferred from label",
            },
            {
                "label": "Używaj cennika",
                "role": "button",
                "meaning": "Toggle or invoke price-list usage.",
                "use_when": "Only when the pricing instruction and current selected state are known.",
                "risk": "pricing setting",
                "evidence": "UIA label observed; meaning inferred from label; exact toggle behavior not verified",
            },
            {
                "label": "Kosztorys/Rysunek",
                "role": "button",
                "meaning": "Open the estimate/drawing-related view.",
                "use_when": "Only when the current workflow requires reviewing the estimate or drawing.",
                "risk": "view/navigation",
                "evidence": "UIA label observed; meaning inferred from label",
            },
            {
                "label": "Operacje magazynowe",
                "role": "button",
                "meaning": "Open warehouse/inventory operations.",
                "avoid_when": "Not needed for ordinary offer creation.",
                "risk": "operational workflow",
                "evidence": "UIA label observed; meaning inferred from label",
            },
            {
                "label": "Sztywność",
                "role": "button",
                "meaning": "Open a stiffness-related construction function.",
                "use_when": "Only if the requested construction needs this function and the current context confirms it.",
                "risk": "specialized construction edit",
                "evidence": "UIA label observed; detailed behavior not verified",
            },
            {
                "label": "Akceptuj",
                "role": "button",
                "meaning": "Accept/confirm the current item or decision.",
                "use_when": "Only when the current dialog/state and requested decision are explicit.",
                "avoid_when": "The target or consequence of acceptance is ambiguous.",
                "risk": "confirmation",
                "evidence": "UIA label observed; meaning depends on owning dialog/context",
            },
            {
                "label": "Odrzuć",
                "role": "button",
                "meaning": "Reject the current item or decision.",
                "use_when": "Only when the user explicitly requested rejection in the current context.",
                "risk": "potentially destructive decision",
                "evidence": "UIA label observed; meaning depends on owning dialog/context",
            },
            {
                "label": "Edytuj załączniki",
                "role": "button",
                "meaning": "Open attachment editing.",
                "use_when": "Only when attachment editing is requested or required.",
                "risk": "edits attachments",
                "evidence": "UIA label observed; meaning inferred from label",
            },
            {
                "label": "Okucia",
                "role": "tabitem",
                "meaning": "Show the hardware/fittings section of a construction editor.",
                "use_when": "Only when the hardware section is the current requested stage.",
                "risk": "section navigation",
                "evidence": "UIA tab label observed; parent context must be checked",
            },
            {
                "label": "Elementy",
                "role": "tabitem",
                "meaning": "Show the elements section within its owning editor.",
                "use_when": "Only when the current stage requires the elements section.",
                "risk": "section navigation",
                "evidence": "UIA tab label observed; parent context must be checked",
            },
            {
                "label": "Statyka",
                "role": "tabitem",
                "meaning": "Show the statics section within its owning editor.",
                "use_when": "Only when the current stage requires the statics section.",
                "risk": "section navigation",
                "evidence": "UIA tab label observed; parent context must be checked",
            },
            {
                "label": "Undo",
                "role": "button",
                "meaning": "Undo the previous edit.",
                "use_when": "Only after an explicit request to undo or a reviewed recovery step.",
                "risk": "changes current editing state",
                "evidence": "UIA label observed; exact visible glyph not independently identified",
            },
            {
                "label": "Redo",
                "role": "button",
                "meaning": "Redo an undone edit.",
                "use_when": "Only after an explicit request to redo or a reviewed recovery step.",
                "risk": "changes current editing state",
                "evidence": "UIA label observed; exact visible glyph not independently identified",
            },
            {
                "label": "Wytnij",
                "role": "button",
                "meaning": "Cut the currently selected content.",
                "use_when": "Only when the intended selection and cut operation are explicit.",
                "risk": "changes clipboard and editing state",
                "evidence": "UIA label observed; exact visible glyph not independently identified",
            },
            {
                "label": "Kopiuj",
                "role": "button",
                "meaning": "Copy the currently selected content.",
                "use_when": "Only when the intended selection is explicit.",
                "risk": "changes clipboard",
                "evidence": "UIA label observed; exact visible glyph not independently identified",
            },
            {
                "label": "Wklej",
                "role": "button",
                "meaning": "Paste clipboard contents into the current selection.",
                "use_when": "Only when destination and pasted content are explicit.",
                "risk": "modifies current content",
                "evidence": "UIA label observed; exact visible glyph not independently identified",
            },
            {
                "label": "Zachowaj",
                "role": "button",
                "meaning": "Save/retain the current state; exact persistence behavior is not yet verified.",
                "use_when": "Only after explicit user authorization to save.",
                "risk": "save/persist data",
                "evidence": "UIA label observed; semantics require live validation",
            },
            {
                "label": "Otwórz",
                "role": "button",
                "meaning": "Open the item or view associated with this specific button.",
                "use_when": "Only after resolving its owning control/group and the intended destination; this label occurs more than once.",
                "risk": "context-dependent navigation",
                "evidence": "Repeated UIA label observed; never resolve by label alone",
            },
            {
                "label": "OK",
                "role": "button",
                "meaning": "Confirm the current dialog/step.",
                "use_when": "Only if a visible OK button belongs to the expected current dialog and the pending choices are validated.",
                "risk": "confirmation",
                "evidence": "Present in documented workflow guidance; must be observed in the current scene",
            },
            {
                "label": "Anuluj",
                "role": "button",
                "meaning": "Cancel the current dialog/step.",
                "use_when": "Only if a visible Anuluj button belongs to the expected current dialog and cancellation is intended.",
                "risk": "cancels current workflow",
                "evidence": "Present in documented workflow guidance; must be observed in the current scene",
            },
        ),
        "icon_learning_policy": (
            "A UIA accessible name and control role are semantic evidence; they do not prove what an unlabeled picture/icon means.",
            "For a control with no usable accessible name, do not guess its meaning from shape, colour, position or proximity alone.",
            "To teach an unknown icon, capture a supervised before/after scene, ask the operator what action the icon represents, and validate the observed state change before storing the mapping.",
            "Persist semantic label, role, owning panel/document, confirmed intent, observed before/after effect, evidence source and confidence only.",
            "Never persist screen coordinates, window handles, AutomationId values or tracked object ids as the semantic identity of an icon.",
            "Never activate save, acceptance, rejection, send/receive or destructive controls merely to discover what they do.",
        ),
    },
    "safety_rules": (
        "Never use coordinates or internal UIA identifiers as model targets.",
        "Never restart a continuation with Nowa oferta.",
        "Never click a control whose explicit document_scope conflicts with the resolved active document.",
        "When Nowa oferta belongs to another document, activate the uniquely identified Start1 tab first, re-observe, and re-resolve the button; never bypass the document-scope guard.",
        "Never choose a generic LayoutItem when a semantic field label cannot be established from UIA structure or other evidence.",
        "Prefer one small GUI mutation at a time and re-observe after it.",
        "Never infer a field solely from ordinal position when multiple controls are ambiguous.",
        "Use visible OK or Anuluj only when those controls are actually present in the current scene.",
        "Business data supplied by the salesperson is authoritative; do not invent missing commercial choices.",
    ),
    "semantic_perception": (
        "WindowHub uses DevExpress WPF layout controls. Generic UIA names "
        "such as LayoutItem can wrap labelled editors. Resolve the semantic "
        "field from parent/child relationships, nearby text labels, and "
        "supported UI Automation properties before exposing it to the "
        "reasoner."
    ),
}


def get_windowhub_offer_knowledge() -> dict[str, object]:
    return WINDOWHUB_OFFER_KNOWLEDGE
