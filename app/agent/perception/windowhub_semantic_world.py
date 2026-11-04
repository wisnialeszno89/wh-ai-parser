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


def enrich_windowhub_scene(scene: ScreenScene) -> ScreenScene:
    """Add model-facing aliases, keep original UIA label for click resolution."""
    if not isinstance(scene, ScreenScene):
        raise TypeError("scene_required")
    state = scene.observation.state
    app = (state.active_application or "").replace("\\", "/").rsplit("/", 1)[-1].casefold()
    title = (state.active_window_title or "").strip().casefold()
    if app != "okna.exe" or title != "właściwości dokumentu":
        return scene
    elements = []
    for e in scene.elements:
        meta = e.metadata or {}
        label = LABELS.get(meta.get("automation_id"))
        if label and meta.get("source") in {"windows_ui_automation", "windowhub_ui_automation"} and meta.get("uia_visible") is True:
            elements.append(replace(e, metadata={**meta, "semantic_label": label}))
        else:
            elements.append(e)
    return replace(scene, elements=tuple(elements))
