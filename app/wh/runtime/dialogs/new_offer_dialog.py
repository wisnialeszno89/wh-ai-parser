"""Read-only semantic map for the first WindowHub new-offer dialog.

The adapter resolves observed UIA controls to stable dialog-field keys. It
never reads field values or executes GUI actions.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Literal

from app.agent.perception.screen_element import ScreenElement


FieldOperation = Literal[
    "lookup",
    "text",
    "number",
    "choice",
    "toggle",
    "date",
    "open_dialog",
]


@dataclass(frozen=True)
class NewOfferFieldSpec:
    """Observed UIA identity and expected semantic role for one dialog field."""

    key: str
    automation_id: str
    operation: FieldOperation
    control_types: frozenset[str]
    ancestor_automation_id: str | None = None


@dataclass(frozen=True)
class NewOfferFieldBinding:
    """A safe target descriptor; never retains the ScreenElement or its values."""

    key: str
    automation_id: str
    operation: FieldOperation
    target_label: str
    control_type: str
    runtime_id: str


@dataclass(frozen=True)
class NewOfferFieldResolution:
    """Fail-closed result of resolving one logical new-offer field."""

    key: str
    status: Literal["resolved", "missing", "ambiguous", "blocked"]
    reason: str
    candidate_count: int = 0
    binding: NewOfferFieldBinding | None = None


class NewOfferDialog:
    """Read-only field resolver for WindowHub's first new-offer dialog.

    Identities and control roles are grounded in the live UIA inventory.
    A field is returned only when exactly one visible, enabled, UIA-backed
    element belongs to the explicitly owned modal and has the expected role.

    Date editors are compound controls. The logical date field is identified
    by its child AutomationId (dateDisplay) together with the parent
    WHCalendar AutomationId. Repeated child ids are never used on their own.
    """

    FIELD_SPECS: tuple[NewOfferFieldSpec, ...] = (
        NewOfferFieldSpec("customer", "IDC_ZAMAWIAJACY", "lookup", frozenset({"button"})),
        NewOfferFieldSpec("contact", "IDC_KONTAKT", "lookup", frozenset({"button"})),
        NewOfferFieldSpec("dealer", "IDC_DEALER", "lookup", frozenset({"button"})),
        NewOfferFieldSpec("delivery", "IDC_DOSTAWA", "lookup", frozenset({"button"})),
        NewOfferFieldSpec("sales_representative", "IDC_OPIEKUN", "text", frozenset({"edit"})),
        NewOfferFieldSpec("discount", "IDC_RABAT", "number", frozenset({"edit"})),
        NewOfferFieldSpec("advance", "IDC_ZALICZKA", "number", frozenset({"edit"})),
        NewOfferFieldSpec("priority", "IDC_PRIORYTET", "choice", frozenset({"combobox"})),
        NewOfferFieldSpec("mounting_system", "IDC_SYSTEM_MONTAZOWY", "choice", frozenset({"combobox"})),
        NewOfferFieldSpec("vat", "IDC_VAT", "choice", frozenset({"combobox"})),
        NewOfferFieldSpec("vat_installation", "IDC_VAT_MONTAZ", "choice", frozenset({"combobox"})),
        NewOfferFieldSpec("vat_accessories", "IDC_VAT_DODATKI", "choice", frozenset({"combobox"})),
        NewOfferFieldSpec("vat_other", "IDC_VAT_INNE", "choice", frozenset({"combobox"})),
        NewOfferFieldSpec("currency", "IDC_WALUTA", "choice", frozenset({"combobox"})),
        NewOfferFieldSpec("certificate_packages", "IDC_PAKIETY_CERT", "toggle", frozenset({"checkbox"})),
        NewOfferFieldSpec("avoid_installation_strips", "IDC_NIE_STOSUJ_LISTW_MONT", "toggle", frozenset({"checkbox"})),
        NewOfferFieldSpec("price_window", "IDC_CENA_OKNA", "toggle", frozenset({"checkbox"})),
        NewOfferFieldSpec("price_installation", "IDC_CENA_MONTAZU", "toggle", frozenset({"checkbox"})),
        NewOfferFieldSpec("price_dismantling", "IDC_CENA_DEMONTAZU", "toggle", frozenset({"checkbox"})),
        NewOfferFieldSpec("price_finishing", "IDC_CENA_WYKONCZENIA", "toggle", frozenset({"checkbox"})),
        NewOfferFieldSpec("price_transport", "IDC_CENA_TRANSPORT", "toggle", frozenset({"checkbox"})),
        NewOfferFieldSpec("price_disposal", "IDC_CENA_LIKWIDACJA", "toggle", frozenset({"checkbox"})),
        NewOfferFieldSpec("sum_total", "IDC_SUMUJ", "toggle", frozenset({"checkbox"})),
        NewOfferFieldSpec("sum_window", "IDC_SUMUJ_OKNO", "toggle", frozenset({"checkbox"})),
        NewOfferFieldSpec("use_dowels", "IDC_STOSUJ_DYBLE", "toggle", frozenset({"checkbox"})),
        NewOfferFieldSpec("dowel_options", "IDC_OPCJE_DYBLI", "open_dialog", frozenset({"button"})),
        NewOfferFieldSpec("realization_date", "dateDisplay", "date", frozenset({"edit"}), "IDC_RELIZACJA"),
        NewOfferFieldSpec("collection_date", "dateDisplay", "date", frozenset({"edit"}), "IDC_ODBIOR"),
        NewOfferFieldSpec("validity_date", "dateDisplay", "date", frozenset({"edit"}), "IDC_WAZNOSC"),
        NewOfferFieldSpec("installation_date", "dateDisplay", "date", frozenset({"edit"}), "IDC_TERMIN_MONTAZU"),
        NewOfferFieldSpec("contract_date", "dateDisplay", "date", frozenset({"edit"}), "IDC_DATA_UMOWY"),
        NewOfferFieldSpec("parapets", "IDC_PARAPETY", "toggle", frozenset({"checkbox"})),
        NewOfferFieldSpec("shutters", "IDC_ROLETY", "toggle", frozenset({"checkbox"})),
        NewOfferFieldSpec("mosquito_nets", "IDC_MOSKITIERY", "toggle", frozenset({"checkbox"})),
        NewOfferFieldSpec("blinds", "IDC_ZALUZJE", "toggle", frozenset({"checkbox"})),
        NewOfferFieldSpec("special_selections", "IDC_DOBORY_SPEC", "toggle", frozenset({"checkbox"})),
        NewOfferFieldSpec("connecting_profiles", "IDC_PROFILE_LACZ", "toggle", frozenset({"checkbox"})),
        NewOfferFieldSpec("finishes", "IDC_WYKONCZENIA", "toggle", frozenset({"checkbox"})),
        NewOfferFieldSpec("air_inlets", "IDC_NAPOWIETRZENIA", "toggle", frozenset({"checkbox"})),
        NewOfferFieldSpec("reference", "IDC_REFERENCJA", "text", frozenset({"edit"})),
        NewOfferFieldSpec("description", "IDC_OPIS", "text", frozenset({"edit"})),
        NewOfferFieldSpec("locations", "IDC_LOKALIZACJE", "open_dialog", frozenset({"button"})),
    )

    _APPROVED_UIA_SOURCES = frozenset({
        "windowhub_ui_automation",
        "windows_ui_automation",
    })

    def resolve_field(
        self,
        scene: object,
        key: str,
    ) -> NewOfferFieldResolution:
        """Resolve one field by exact UIA AutomationId metadata only."""
        normalized_key = key.strip().casefold() if isinstance(key, str) else ""
        spec = next(
            (item for item in self.FIELD_SPECS if item.key == normalized_key),
            None,
        )
        if spec is None:
            return NewOfferFieldResolution(
                key=normalized_key,
                status="missing",
                reason="Unknown new-offer field key.",
            )

        elements = tuple(getattr(scene, "elements", ()) or ())
        candidates = [
            element
            for element in elements
            if self._matches_spec_identity(element, spec)
        ]
        candidates = self._collapse_same_runtime_modal_duplicates(candidates)
        if not candidates:
            return NewOfferFieldResolution(
                key=spec.key,
                status="missing",
                reason="No semantic UIA element matched the observed field identity.",
            )
        if len(candidates) != 1:
            return NewOfferFieldResolution(
                key=spec.key,
                status="ambiguous",
                reason="More than one semantic UIA element matched the field identity.",
                candidate_count=len(candidates),
            )

        element = candidates[0]
        metadata = getattr(element, "metadata", None)
        if not isinstance(metadata, Mapping):
            return self._blocked(spec, "Field metadata is unavailable.")

        if metadata.get("uia_owned_modal") is not True:
            return self._blocked(spec, "Field is not proven to belong to a WindowHub-owned modal.")
        if not self._has_uia_provenance(metadata):
            return self._blocked(spec, "Field has no approved UI Automation provenance.")
        if metadata.get("uia_visible") is not True:
            return self._blocked(spec, "Field is not confirmed visible.")
        if metadata.get("uia_enabled") is not True:
            return self._blocked(spec, "Field is not confirmed enabled.")

        runtime_id = metadata.get("uia_runtime_id")
        if not isinstance(runtime_id, str) or not runtime_id.strip():
            return self._blocked(spec, "Field has no stable UIA RuntimeId.")

        raw_kind = metadata.get("uia_control_type")
        if not isinstance(raw_kind, str) or not raw_kind.strip():
            raw_kind = getattr(element, "kind", "")
        kind = str(raw_kind).strip().casefold()
        if kind not in spec.control_types:
            return self._blocked(
                spec,
                f"Field role mismatch: expected {sorted(spec.control_types)}, observed {kind!r}.",
            )

        return NewOfferFieldResolution(
            key=spec.key,
            status="resolved",
            reason="Unique enabled, visible, UIA-backed control found in the owned new-offer dialog.",
            candidate_count=1,
            binding=NewOfferFieldBinding(
                key=spec.key,
                automation_id=spec.automation_id,
                operation=spec.operation,
                target_label=str(getattr(element, "label", "") or ""),
                control_type=kind,
                runtime_id=runtime_id,
            ),
        )

    def resolve_all(self, scene: object) -> tuple[NewOfferFieldResolution, ...]:
        """Return a read-only resolution result for every declared dialog field."""
        return tuple(
            self.resolve_field(scene, spec.key)
            for spec in self.FIELD_SPECS
        )

    @classmethod
    def _collapse_same_runtime_modal_duplicates(
        cls,
        candidates: list[ScreenElement],
    ) -> list[ScreenElement]:
        """Keep the owned-modal representation of the same UIA RuntimeId.

        WindowHub's root window and its owned dialog can both enumerate the
        same descendant. Collapse only candidates with the exact same
        non-empty UIA RuntimeId. Prefer the one explicitly marked as owned
        modal. Different RuntimeIds are never collapsed just because their
        AutomationIds match.
        """
        groups: dict[str, list[ScreenElement]] = {}
        without_runtime_id: list[ScreenElement] = []

        for element in candidates:
            metadata = getattr(element, "metadata", None)
            runtime_id = (
                metadata.get("uia_runtime_id")
                if isinstance(metadata, Mapping)
                else None
            )
            if isinstance(runtime_id, str) and runtime_id.strip():
                groups.setdefault(runtime_id, []).append(element)
            else:
                without_runtime_id.append(element)

        collapsed = list(without_runtime_id)
        for group in groups.values():
            if len(group) == 1:
                collapsed.append(group[0])
                continue

            modal = [
                element
                for element in group
                if (
                    isinstance(getattr(element, "metadata", None), Mapping)
                    and element.metadata.get("uia_owned_modal") is True
                )
            ]
            if len(modal) == 1:
                collapsed.append(modal[0])
            else:
                # Without one unique owned-modal representative, retain the
                # ambiguity instead of choosing by enumeration order.
                collapsed.extend(group)

        return collapsed

    @staticmethod
    def _ancestor_has_automation_id(metadata: Mapping, automation_id: str) -> bool:
        context = metadata.get("uia_ancestor_context")
        if not isinstance(context, (tuple, list)):
            return False
        for ancestor in context:
            if not isinstance(ancestor, (tuple, list)) or len(ancestor) < 4:
                continue
            # Provider contract: control type, class, name, AutomationId, HWND.
            if ancestor[3] == automation_id:
                return True
        return False

    @classmethod
    def _matches_spec_identity(
        cls,
        element: ScreenElement,
        spec: NewOfferFieldSpec,
    ) -> bool:
        metadata = getattr(element, "metadata", None)
        if not isinstance(metadata, Mapping):
            return False

        direct_id = metadata.get("automation_id")
        if spec.ancestor_automation_id is None:
            return direct_id == spec.automation_id

        return (
            direct_id == spec.automation_id
            and cls._ancestor_has_automation_id(
                metadata,
                spec.ancestor_automation_id,
            )
        )

    @classmethod
    def _has_uia_provenance(cls, metadata: Mapping) -> bool:
        if metadata.get("source") in cls._APPROVED_UIA_SOURCES:
            return True
        fusion_sources = metadata.get("fusion_sources") or ()
        if isinstance(fusion_sources, str):
            fusion_sources = (fusion_sources,)
        if not isinstance(fusion_sources, (tuple, list, set, frozenset)):
            return False
        return any(
            source in cls._APPROVED_UIA_SOURCES
            for source in fusion_sources
        )

    @staticmethod
    def _blocked(
        spec: NewOfferFieldSpec,
        reason: str,
    ) -> NewOfferFieldResolution:
        return NewOfferFieldResolution(
            key=spec.key,
            status="blocked",
            reason=reason,
            candidate_count=1,
        )
