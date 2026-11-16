"""Semantic labels for WindowHub UIA controls; native IDs never sent to a model."""
from dataclasses import replace
from app.agent.perception.screen_scene import ScreenScene

LABELS = {
    "IDC_ZAMAWIAJACY": "Wybierz istniejącego klienta",
    "IDC_NEW": "Dodaj nowego klienta",
    "IDC_CENA_OKNA": "Bez ceny konstrukcji",
    "IDC_CENA_MONTAZU": "Bez ceny montażu",
    "IDC_CENA_DEMONTAZU": "Bez ceny demontażu",
    "IDC_CENA_WYKONCZENIA": "Bez ceny wykończenia",
    "IDC_FILTER": "Filtr klientów",
    "IDC_EDYCJA": "Edytuj klienta",
    "IDC_SHOW_ALL": "Pokaż wszystkich klientów",
}


WIZARD_MEANINGS = {
    "quantity_input": "Liczba sztuk pozycji",
    "width_1": "Szerokość całego okna",
    "height_1": "Wysokość całego okna",
    "profile_color": "Kolor profilu okiennego",
    "profile_system_picker": "Wybierz system profili",
    "glazing_package": "Pakiet szybowy",
    "spacer_frame": "Ramka dystansowa",
}


def enrich_windowhub_scene(scene: ScreenScene) -> ScreenScene:
    """Explain uniquely matched native controls without changing executable UIA labels."""
    if not isinstance(scene, ScreenScene):
        raise TypeError("scene_required")
    state = scene.observation.state
    app = (state.active_application or "").replace("\\", "/").rsplit("/", 1)[-1].casefold()
    if app != "okna.exe":
        return scene
    title = (state.active_window_title or "").strip().casefold()
    aliases: dict[int, str] = {}
    if title == "właściwości dokumentu":
        for element in scene.elements:
            metadata = element.metadata or {}
            label = LABELS.get(metadata.get("automation_id"))
            if (
                label
                and metadata.get("source") in {"windows_ui_automation", "windowhub_ui_automation"}
                and metadata.get("uia_visible") is True
            ):
                aliases[id(element)] = label
    else:
        # Reuse the existing verified wizard field map. The model sees what a
        # field means; its original Name, RuntimeId and AutomationId remain local.
        from app.agent.offers.windowhub_offer_form_map import WindowHubOfferFormMap
        snapshot = WindowHubOfferFormMap().inspect(scene)
        if snapshot is not None:
            for field in snapshot.fields:
                label = WIZARD_MEANINGS.get(field.field_name)
                if label and field.is_unique and field.enabled is True:
                    aliases[id(field.element)] = label
    # Scope the meaning of Dodaj by the selected MDI document, not by a
    # global count of identically named controls from other open offers.
    if title.startswith("okna - ofr/"):
        from app.agent.runtime.active_document_scope import unique_active_document_control
        element = unique_active_document_control(scene, label="Dodaj")
        if element is not None:
            meta = element.metadata or {}
            runtime_id = meta.get("uia_runtime_id")
            if (
                isinstance(runtime_id, str) and runtime_id.strip()
                and sum(
                    1 for item in scene.elements
                    if (item.metadata or {}).get("source") in {
                        "windows_ui_automation", "windowhub_ui_automation"
                    } and (item.metadata or {}).get("uia_runtime_id") == runtime_id
                ) == 1
            ):
                aliases[id(element)] = "Dodaj nową pozycję okna do oferty"
    if not aliases:
        return scene
    elements = tuple(
        replace(e, metadata={**(e.metadata or {}), "semantic_label": aliases[id(e)]})
        if id(e) in aliases else e
        for e in scene.elements
    )
    return replace(scene, elements=elements)
