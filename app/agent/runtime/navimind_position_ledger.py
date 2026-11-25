"""Immutable multi-position source manifest and fail-closed execution ledger.

A manifest is built locally from the *complete extracted* inbox on the GUI
thread at the user's explicit AI-consent gesture. It is not transmitted by
itself. Position IDs are source-scoped, so repeated sizes stay distinct.
A verified position readback is mandatory before advancing to a new position.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from hashlib import sha256
import re

MAX_POSITIONS = 80

_CATALOG_LABELS = {
    "profil": "profile",
    "profile": "profile",
    "profilsystem": "profile",
    "system profili": "profile",
    "farbe innen": "color_inside",
    "kolor wewnętrzny": "color_inside",
    "kolor wewnetrzny": "color_inside",
    "farbe außen": "color_outside",
    "farbe aussen": "color_outside",
    "kolor zewnętrzny": "color_outside",
    "kolor zewnetrzny": "color_outside",
    "verglasung": "glazing",
    "pakiet szybowy": "glazing",
    "szyby": "glazing",
    "beschlag": "hardware",
    "okucia": "hardware",
    "ramka dystansowa": "spacer",
}


def extract_explicit_catalog_requirements(
    source_lines: tuple[str, ...] | list[str],
) -> tuple[tuple[str, str], ...]:
    """Source-scoped labelled requirements, not inferred WH database codes."""
    values: dict[str, set[str]] = {}
    for line in source_lines:
        for clause in str(line).split(";"):
            if ":" not in clause:
                continue
            label, value = clause.split(":", 1)
            key = _CATALOG_LABELS.get(" ".join(label.strip().casefold().split()))
            value = " ".join(value.strip().split())
            if key and 1 <= len(value) <= 100:
                values.setdefault(key, set()).add(value)
    return tuple(
        (key, next(iter(entries)) if len(entries) == 1 else "")
        for key, entries in sorted(values.items())
    )


@dataclass(frozen=True)
class SourcePosition:
    position_id: str
    source_index: int
    ordinal: int
    product_type: str
    width_mm: int | None
    height_mm: int | None
    quantity: int | None
    opening: str | None
    source_fingerprint: str
    snippet: str
    issues: tuple[str, ...] = ()
    catalogue_requirements: tuple[tuple[str, str], ...] = ()

    @property
    def ready_for_geometry(self) -> bool:
        return (
            self.product_type == "window"
            and type(self.width_mm) is int and 200 <= self.width_mm <= 5000
            and type(self.height_mm) is int and 200 <= self.height_mm <= 5000
            and not self.issues
        )


@dataclass(frozen=True)
class PositionManifest:
    positions: tuple[SourcePosition, ...]
    incomplete_sources: tuple[int, ...] = ()
    unparsed_sources: tuple[int, ...] = ()
    overflow: bool = False

    @property
    def safe_to_sequence(self) -> bool:
        return (
            bool(self.positions) and not self.incomplete_sources
            and not self.unparsed_sources and not self.overflow
        )


_NUMBERED_POSITION = re.compile(
    r"^\s*(?:pos(?:ition)?\.?\s*#?\s*\d+|\d{1,3}[.)])"
    r"\s*[:.)-]?\s*(?=(?:[1-9][0-9]?\s*"
    r"(?:stk\.?|stück|szt\.?)\s+)?"
    r"(?:fenster|haustür|haustuer|kippfenster|hst[- ]tür|psk[- ]tür)\b)",
    re.IGNORECASE,
)


def _normalize_numbered_headings(body: str) -> tuple[str, int]:
    """Recognize explicit 'Pos. 1: 2 Stk Fenster ...' lines, not prose."""
    lines = []
    matched = 0
    for line in body.splitlines():
        changed, count = _NUMBERED_POSITION.subn("", line, count=1)
        if count:
            matched += 1
        lines.append(changed if count else line)
    return "\n".join(lines), matched


def build_position_manifest(inbox) -> PositionManifest:
    """Parse every source separately; never derive position IDs from dimensions."""
    from app.agent.intake.german_offer_mail import inspect_german_offer_mail
    sources: list[tuple[str, bool]] = []
    pasted = getattr(inbox, "pasted_text", "")
    if isinstance(pasted, str) and pasted.strip():
        sources.append((pasted, False))
    for source in getattr(inbox, "sources", ()):
        body = getattr(source, "text", "")
        sources.append((
            body if isinstance(body, str) else "",
            bool(getattr(source, "truncated", False)
                 or getattr(source, "needs_ocr", False)
                 or not isinstance(body, str) or not body.strip()),
        ))
    result = []
    incomplete = []
    unparsed = []
    overflow = False
    for number, (body, partial) in enumerate(sources, 1):
        if partial:
            incomplete.append(number)
        normalized, numbered_count = _normalize_numbered_headings(body)
        try:
            matches = inspect_german_offer_mail(normalized)
        except (TypeError, ValueError, AttributeError):
            matches = []
        # Do not silently ignore any explicitly numbered position. Even
        # an otherwise valid parser result is unsafe if it skipped a row.
        if not matches or (numbered_count and len(matches) < numbered_count):
            unparsed.append(number)
        for ordinal, match in enumerate(matches, 1):
            if len(result) >= MAX_POSITIONS:
                overflow = True
                break
            if not isinstance(match, dict):
                overflow = True
                break
            lines = match.get("source_lines") or ()
            snippet = " | ".join(str(line).strip() for line in lines)[:460]
            product = match.get("product_type")
            width = match.get("width_mm")
            height = match.get("height_mm")
            qty = match.get("quantity")
            opening = match.get("opening")
            catalog = extract_explicit_catalog_requirements(
                tuple(str(line) for line in lines)
            )
            issues = []
            if any(not value for _, value in catalog):
                issues.append("conflicting_catalogue_requirements")
            if product != "window":
                issues.append("product_requires_separate_catalogue_route")
            if type(width) is not int or type(height) is not int:
                issues.append("dimensions_missing_or_conflicting")
            if type(qty) is not int or qty <= 0:
                issues.append("quantity_missing_or_conflicting")
            if match.get("opening_mode") == "conflicting":
                issues.append("opening_conflicting")
            if match.get("proposed_variants"):
                issues.append("variants_require_choice")
            if not snippet:
                issues.append("source_lines_missing")
            fingerprint = sha256(
                (str(number) + "\n" + str(ordinal) + "\n"
                 + repr(match)).encode("utf-8")
            ).hexdigest()[:20]
            result.append(SourcePosition(
                position_id=f"S{number:02d}-P{ordinal:03d}",
                source_index=number,
                ordinal=ordinal,
                product_type=str(product or "unknown"),
                width_mm=width if type(width) is int else None,
                height_mm=height if type(height) is int else None,
                quantity=qty if type(qty) is int else None,
                opening=str(opening) if opening else None,
                source_fingerprint=fingerprint,
                snippet=snippet,
                issues=tuple(issues),
                catalogue_requirements=catalog,
            ))
        if overflow:
            break
    return PositionManifest(
        tuple(result), tuple(incomplete), tuple(unparsed), overflow,
    )


@dataclass(frozen=True)
class PositionCheckpoint:
    position_id: str
    document_key: str
    width_mm: int
    height_mm: int
    quantity: int
    independent_readback: bool
    construction_verified: bool
    signature: str


@dataclass(frozen=True)
class PositionLedger:
    manifest: PositionManifest
    active_index: int = 0
    completed: tuple[PositionCheckpoint, ...] = ()

    @property
    def active(self) -> SourcePosition | None:
        if not 0 <= self.active_index < len(self.manifest.positions):
            return None
        return self.manifest.positions[self.active_index]

    @property
    def finished(self) -> bool:
        return self.active_index == len(self.manifest.positions) and bool(self.completed)

    def complete_verified(
        self, checkpoint: PositionCheckpoint, *, pinned_document: str,
    ) -> "PositionLedger":
        """Only independently observed and uniquely pinned result advances.

        Model 'done', wizard stage transition or an earlier screenshot alone
        cannot produce a checkpoint. The integration caller must validate a
        fresh native WindowHub readback before calling this method.
        """
        current = self.active
        if current is None:
            raise ValueError("no_active_position_to_complete")
        if not self.manifest.safe_to_sequence or not current.ready_for_geometry:
            raise ValueError("source_manifest_not_verified")
        if (not checkpoint.independent_readback
                or not checkpoint.construction_verified
                or not checkpoint.signature
                or checkpoint.document_key != pinned_document
                or checkpoint.position_id != current.position_id
                or checkpoint.width_mm != current.width_mm
                or checkpoint.height_mm != current.height_mm
                or checkpoint.quantity != current.quantity):
            raise ValueError("position_readback_not_verified")
        if any(x.position_id == checkpoint.position_id for x in self.completed):
            raise ValueError("duplicate_position_completion")
        return replace(
            self, completed=(*self.completed, checkpoint),
            active_index=self.active_index + 1,
        )


def position_prompt(position: SourcePosition, *, index: int, total: int) -> str:
    """One source-scoped position per V2 cycle, never mix neighbour values."""
    return (
        f"AKTYWNA POZYCJA {index + 1}/{total}: {position.position_id}; "
        f"typ={position.product_type}; "
        f"szerokość={position.width_mm} mm; "
        f"wysokość={position.height_mm} mm; "
        f"ilość={position.quantity}; "
        f"otwieranie={position.opening or 'nieokreślone'}.\n"
        f"DOWÓD ZE ŹRÓDŁA {position.source_index}: {position.snippet}\n"
        "WYMAGANIA KATALOGOWE (jawnie opisane w źródle): "
        + (", ".join(f"{name}={value}" for name, value in
                     position.catalogue_requirements) or "nieokreślone")
        + "\n"
        "Nie przenoś danych z innych pozycji. "
        "Nie uznawaj pozycji za wykonaną bez niezależnego odczytu "
        "konstrukcji i ilości. Nie zapisuj ani nie wysyłaj oferty."
    )


def validate_bound_position_entry(
    position: SourcePosition, *, field_name: str, proposed_value: str,
) -> tuple[bool, str]:
    """Bind every numeric write to exactly one source-scoped position.

    Do not search for a matching number in the entire multi-position email.
    """
    if not position.ready_for_geometry or type(position.quantity) is not int:
        return False, "active_source_position_incomplete"
    if field_name == "description_input":
        # Only a verbatim fragment from THIS position, not a generated
        # description borrowed from a neighbouring window or customer.
        if not isinstance(proposed_value, str):
            return False, "description_value_not_text"
        text = " ".join(proposed_value.casefold().split())
        source = " ".join(position.snippet.casefold().split())
        if 4 <= len(text) <= 160 and text in source:
            return True, "description_verbatim_active_position_source"
        return False, "description_not_found_in_active_source"
    expected = {
        "width_1": position.width_mm,
        "height_1": position.height_mm,
        "quantity_input": position.quantity,
    }
    if field_name not in expected:
        return False, "active_position_field_requires_manual_review"
    if not isinstance(proposed_value, str):
        return False, "proposed_value_is_not_text"
    if proposed_value.strip() != str(expected[field_name]):
        return False, "value_does_not_match_active_source_position"
    return True, "value_matches_active_source_position"


def manifest_blocker_summary(manifest: PositionManifest) -> str:
    """Actionable, PII-free explanation of why an enquiry needs review."""
    problems = []
    if manifest.overflow:
        problems.append(
            f"wykryto więcej niż {MAX_POSITIONS} pozycji; "
            "żadna pozostała pozycja nie może zostać pominięta"
        )
    if manifest.incomplete_sources:
        ids = ", ".join(str(x) for x in manifest.incomplete_sources[:10])
        problems.append(
            f"źródła {ids}: skan, ucięty tekst lub brak OCR"
        )
    if manifest.unparsed_sources:
        ids = ", ".join(str(x) for x in manifest.unparsed_sources[:10])
        problems.append(
            f"źródła {ids}: nie rozpoznano wszystkich pozycji"
        )
    for position in manifest.positions:
        if position.issues:
            problems.append(
                position.position_id + ": " + ", ".join(position.issues[:3])
            )
        if len(problems) >= 8:
            break
    if not manifest.positions:
        problems.append("brak pozycji rozpoznanych z zatwierdzonych źródeł")
    return "; ".join(problems)[:900] if problems else "brak blokad źródłowych"


def two_window_test_gate(inbox) -> tuple[bool, str]:
    """Fail closed unless source approval can represent exactly two windows.

    Use after operator has saved local text/PDF; this function is read-only
    and never grants document/model consent or GUI action permission.
    """
    manifest = build_position_manifest(inbox)
    if not manifest.safe_to_sequence:
        return False, "two_window_source_incomplete_or_unparsed"
    if len(manifest.positions) != 2:
        return False, "two_window_position_count_not_two"
    if any(
        p.product_type != "window" or not p.ready_for_geometry
        for p in manifest.positions
    ):
        return False, "two_window_position_geometry_or_quantity_ambiguous"
    if len({p.position_id for p in manifest.positions}) != 2:
        return False, "two_window_position_identity_not_unique"
    return True, "exactly_two_source_scoped_windows_ready_for_review"
