"""Read-only mapping of observed WindowHub new-item wizard controls.

The map describes stable UI Automation selectors per wizard step. It never
reads or writes field values and never performs desktop actions.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import unicodedata

from app.agent.perception.screen_element import ScreenElement
from app.agent.perception.screen_scene import ScreenScene


_UIA_SOURCES = frozenset(
    {
        "windows_ui_automation",
        "windowhub_ui_automation",
    }
)


class WindowHubFormStep(str, Enum):
    POSITION = "position"
    DIMENSIONS = "dimensions"
    BASIC_PARAMETERS = "basic_parameters"
    GLAZING = "glazing"
    SILL = "sill"
    HARDWARE = "hardware"


@dataclass(frozen=True)
class WindowHubControlSpec:
    """One observed control, scoped to a specific wizard step."""

    field_name: str
    step: WindowHubFormStep
    control_type: str
    label: str
    automation_id: str | None


@dataclass(frozen=True)
class WindowHubFieldMatch:
    """Read-only result for one logical field in the current UIA scene."""

    field_name: str
    status: str
    element: ScreenElement | None
    candidate_count: int
    enabled: bool | None

    @property
    def is_unique(self) -> bool:
        return self.status == "matched" and self.element is not None


@dataclass(frozen=True)
class WindowHubOfferFormSnapshot:
    """Known controls for one currently observed WindowHub wizard step."""

    step: WindowHubFormStep
    window_title: str
    fields: tuple[WindowHubFieldMatch, ...]

    def field(self, field_name: str) -> WindowHubFieldMatch | None:
        return next(
            (
                item
                for item in self.fields
                if item.field_name == field_name
            ),
            None,
        )


def normalize_uia_text(value: str) -> str:
    """Normalize UIA names and window titles without locale-dependent rules."""
    decomposed = unicodedata.normalize("NFKD", value.casefold())
    without_marks = "".join(
        char for char in decomposed
        if not unicodedata.combining(char)
    )
    return " ".join(
        without_marks.replace("ł", "l").split()
    )


_STEP_TITLES = {
    WindowHubFormStep.POSITION: ("Dodawanie nowej pozycji",),
    WindowHubFormStep.DIMENSIONS: ("Wielkość okna",),
    WindowHubFormStep.BASIC_PARAMETERS: ("Podstawowe parametry okna",),
    WindowHubFormStep.GLAZING: ("Parametry szklenia",),
    WindowHubFormStep.SILL: ("Parametry parapetu",),
    WindowHubFormStep.HARDWARE: ("Parametry okuć",),
}

_TITLE_TO_STEP = {
    normalize_uia_text(title): step
    for step, titles in _STEP_TITLES.items()
    for title in titles
}


def identify_windowhub_form_step(title: str | None) -> WindowHubFormStep | None:
    if not isinstance(title, str) or not title.strip():
        return None
    return _TITLE_TO_STEP.get(normalize_uia_text(title))


def _spec(
    step: WindowHubFormStep,
    field_name: str,
    control_type: str,
    label: str,
    automation_id: str | None,
) -> WindowHubControlSpec:
    return WindowHubControlSpec(
        field_name=field_name,
        step=step,
        control_type=control_type,
        label=label,
        automation_id=automation_id,
    )


_POSITION = WindowHubFormStep.POSITION
_DIMENSIONS = WindowHubFormStep.DIMENSIONS
_BASIC = WindowHubFormStep.BASIC_PARAMETERS
_GLAZING = WindowHubFormStep.GLAZING
_SILL = WindowHubFormStep.SILL
_HARDWARE = WindowHubFormStep.HARDWARE


WINDOWHUB_OFFER_CONTROL_SPECS = (
    # Item type and shared fields.
    _spec(_POSITION, "item_type_window", "radiobutton", "Okno", "1329"),
    _spec(_POSITION, "item_type_sill", "radiobutton", "Parapet", "1330"),
    _spec(_POSITION, "item_type_shutter", "radiobutton", "Roleta", "1331"),
    _spec(_POSITION, "item_type_glazing", "radiobutton", "Szklenie", "1332"),
    _spec(_POSITION, "item_type_other", "radiobutton", "Inne artykuły", "1333"),
    _spec(_POSITION, "item_type_door", "radiobutton", "Drzwi", "1335"),
    _spec(_POSITION, "item_type_hardware", "radiobutton", "Okucia", "1336"),
    _spec(_POSITION, "item_type_catalog", "radiobutton", "Z cennika", "1337"),
    _spec(_POSITION, "item_type_text", "radiobutton", "Pozycja tekstowa", "1338"),
    _spec(_POSITION, "item_type_mosquito_screen", "radiobutton", "Moskitiera", "1339"),
    _spec(_POSITION, "item_type_blind", "radiobutton", "Żaluzja", "1340"),
    _spec(_POSITION, "item_type_joining_profile", "radiobutton", "Profil łączący", "1341"),
    _spec(_POSITION, "item_type_filling", "radiobutton", "Wypełnienie", "1342"),
    _spec(_POSITION, "item_type_sliding_door", "radiobutton", "Drzwi przesuwne", "1344"),
    _spec(_POSITION, "item_type_calculated_other", "radiobutton", "Inny artykuł (kalkulacja)", "1345"),
    _spec(_POSITION, "item_type_garage_door", "radiobutton", "Brama", "1347"),
    _spec(_POSITION, "item_type_cassonetto", "radiobutton", "Cassonetto", "1348"),
    _spec(_POSITION, "item_from_gallery", "checkbox", "Z galerii", "1367"),
    _spec(_POSITION, "quantity_selector", "combobox", "Ile sztuk", "1334"),
    _spec(_POSITION, "quantity_input", "edit", "Ile sztuk", "1001"),
    _spec(_POSITION, "description_selector", "combobox", "Opis pozycji", "1672"),
    _spec(_POSITION, "description_input", "edit", "Opis pozycji", "1001"),

    # Five visible width/height pairs. Their meaning is deliberately kept
    # slot-based until the WindowHub layout semantics are verified.
    _spec(_DIMENSIONS, "width_1", "edit", "Szerokość", "1000"),
    _spec(_DIMENSIONS, "height_1", "edit", "Wysokość", "1001"),
    _spec(_DIMENSIONS, "width_2", "edit", "Szerokość", "1014"),
    _spec(_DIMENSIONS, "height_2", "edit", "Wysokość", "1015"),
    _spec(_DIMENSIONS, "width_3", "edit", "Szerokość", "1022"),
    _spec(_DIMENSIONS, "height_3", "edit", "Wysokość", "1023"),
    _spec(_DIMENSIONS, "width_4", "edit", "Szerokość", "1026"),
    _spec(_DIMENSIONS, "height_4", "edit", "Wysokość", "1027"),
    _spec(_DIMENSIONS, "width_5", "edit", "Szerokość", "1024"),
    _spec(_DIMENSIONS, "height_5", "edit", "Wysokość", "1025"),

    # Basic window/profile parameters.
    _spec(_BASIC, "profile_color", "combobox", "Wybierz kolor profili", "1054"),
    _spec(_BASIC, "reinforcement_a", "radiobutton", "A - najsłabsze", "1329"),
    _spec(_BASIC, "reinforcement_b", "radiobutton", "B", "1330"),
    _spec(_BASIC, "reinforcement_c", "radiobutton", "C", "1331"),
    _spec(_BASIC, "reinforcement_d", "radiobutton", "D", "1332"),
    _spec(_BASIC, "reinforcement_e", "radiobutton", "E", "1333"),
    _spec(_BASIC, "reinforcement_f", "radiobutton", "F - najmocniejsze", "1334"),
    _spec(_BASIC, "reinforcement_none", "radiobutton", "brak wzmocnienia - nie polecane", "1335"),
    _spec(_BASIC, "reinforcement_automatic", "radiobutton", "dobór automatyczny", "1336"),
    _spec(_BASIC, "reinforcement_automatic_max", "radiobutton", "dobór automatyczny MAX", "1337"),
    _spec(_BASIC, "reinforcement_category", "combobox", "Wybierz kategorię wzmocnienia", "1831"),
    _spec(_BASIC, "profile_system_picker", "button", "Wybierz system profili", None),

    # Glazing parameters.
    _spec(_GLAZING, "glazing_package", "combobox", "Wybierz typ pakietu szybowego", "1033"),
    _spec(_GLAZING, "glazing_details", "button", "Parametry szklenia", "1020"),
    _spec(_GLAZING, "spacer_frame", "combobox", "Ramka dystansowa", "1035"),
    _spec(_GLAZING, "spacer_frame_color", "combobox", "Kolor ramki dystansowej", "1034"),

    # Optional sill parameters, observed in the wizard.
    _spec(_SILL, "sill_type", "combobox", "Wybierz typ", "1227"),
    _spec(_SILL, "sill_width_selector", "combobox", "Szerokość", "1664"),
    _spec(_SILL, "sill_width_input", "edit", "Szerokość", "1001"),
    _spec(_SILL, "sill_color", "combobox", "Wybierz kolor", "1054"),
    _spec(_SILL, "sill_length_with_endcaps", "edit", "Długość z zaślepkami", "1388"),
    _spec(_SILL, "sill_joining_profile_color", "combobox", "Wybierz kolor profilu łączącego parapet", "1379"),
    _spec(_SILL, "sill_without_endcap", "checkbox", "Bez zaślepki", "1049"),
    _spec(_SILL, "sill_endcap", "combobox", "Zaślepka", "1820"),
    _spec(_SILL, "sill_finishes", "checkbox", "Wykończenia", "1569"),
    _spec(_SILL, "sill_installed", "checkbox", "Montowany", "1050"),

    # Optional hardware parameters, observed in the wizard.
    _spec(_HARDWARE, "hardware_profile", "combobox", "Wybierz profil", "1012"),
    _spec(_HARDWARE, "hardware_group", "combobox", "Wybierz grupę", "1013"),
    _spec(_HARDWARE, "hardware_inner_color", "combobox", "Wybierz kolor", "1054"),
    _spec(_HARDWARE, "hardware_outer_color", "combobox", "Wybierz kolor zewnętrzny", "1545"),
    _spec(_HARDWARE, "locking_interval", "edit", "Rygluj co", "3645"),
    _spec(_HARDWARE, "backset", "combobox", "Dornmass", "1153"),
    _spec(_HARDWARE, "rebate_type", "combobox", "Rodzaj wrębu", "1154"),
    _spec(_HARDWARE, "faceplate_strip", "combobox", "Listwa czołowa", "3676"),
    _spec(_HARDWARE, "handle_spindle_length_selector", "combobox", "Długość trzpienia klamki", "1155"),
    _spec(_HARDWARE, "handle_spindle_length_input", "edit", "Długość trzpienia klamki", "1001"),
    _spec(_HARDWARE, "rebate_from_stop", "edit", "Wrąb od przylgi", "1156"),
)


class WindowHubOfferFormMap:
    """Resolve logical fields only against the matching, currently visible UIA step."""

    def __init__(self, specs=WINDOWHUB_OFFER_CONTROL_SPECS) -> None:
        self._specs = tuple(specs)

    @staticmethod
    def identify_step(title: str | None) -> WindowHubFormStep | None:
        return identify_windowhub_form_step(title)

    def specs_for_step(
        self,
        step: WindowHubFormStep,
    ) -> tuple[WindowHubControlSpec, ...]:
        return tuple(
            spec for spec in self._specs
            if spec.step == step
        )

    def inspect(
        self,
        scene: ScreenScene,
    ) -> WindowHubOfferFormSnapshot | None:
        if not isinstance(scene, ScreenScene):
            raise TypeError("windowhub_offer_form_scene_invalid")

        active_application = scene.observation.state.active_application
        process_name = (
            active_application.replace("\\", "/").rsplit("/", 1)[-1].casefold()
            if isinstance(active_application, str)
            else ""
        )
        if process_name != "okna.exe":
            return None

        title = scene.observation.state.active_window_title or ""
        step = self.identify_step(title)
        if step is None:
            return None

        fields = tuple(
            self._match_spec(scene, spec)
            for spec in self.specs_for_step(step)
        )
        return WindowHubOfferFormSnapshot(
            step=step,
            window_title=title,
            fields=fields,
        )

    def resolve(
        self,
        scene: ScreenScene,
        field_name: str,
    ) -> WindowHubFieldMatch | None:
        snapshot = self.inspect(scene)
        if snapshot is None:
            return None
        return snapshot.field(field_name)

    @staticmethod
    def _match_spec(
        scene: ScreenScene,
        spec: WindowHubControlSpec,
    ) -> WindowHubFieldMatch:
        expected_label = normalize_uia_text(spec.label)
        candidates = []
        for element in scene.elements:
            if element.kind.casefold() != spec.control_type:
                continue
            if not isinstance(element.label, str):
                continue
            if normalize_uia_text(element.label) != expected_label:
                continue

            metadata = element.metadata or {}
            if metadata.get("source") not in _UIA_SOURCES:
                continue
            if metadata.get("uia_visible") is not True:
                continue

            if spec.automation_id is not None:
                actual_id = metadata.get("automation_id")
                if (
                    not isinstance(actual_id, str)
                    or actual_id.casefold() != spec.automation_id.casefold()
                ):
                    continue
            candidates.append(element)

        if not candidates:
            return WindowHubFieldMatch(
                field_name=spec.field_name,
                status="missing",
                element=None,
                candidate_count=0,
                enabled=None,
            )
        if len(candidates) != 1:
            return WindowHubFieldMatch(
                field_name=spec.field_name,
                status="ambiguous",
                element=None,
                candidate_count=len(candidates),
                enabled=None,
            )

        element = candidates[0]
        enabled = (element.metadata or {}).get("uia_enabled")
        return WindowHubFieldMatch(
            field_name=spec.field_name,
            status="matched",
            element=element,
            candidate_count=1,
            enabled=enabled if isinstance(enabled, bool) else None,
        )
