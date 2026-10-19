from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
import math
import re
from typing import Iterable, Mapping

from app.agent.learning.learned_parameter import canonical_parameter_name
from app.agent.offers.offer_context import OfferContext
from app.agent.offers.offer_context_parser import OfferContextParser
from app.agent.offers.offer_context_validator import OfferContextValidator
from app.agent.offers.profile_selection import ProfileSelectionSource


QUOTE_FACTS_VERSION = "1"
_QUOTE_FIELDS = frozenset(
    {
        "product_type",
        "width",
        "height",
        "quantity",
        "profile",
        "configuration",
        "opening",
        "glazing",
        "color_inside",
        "color_outside",
        "price",
    }
)
_FIELD_ALIASES = {
    "produkt": "product_type",
    "produkt_typ": "product_type",
    "szerokosc": "width",
    "wysokosc": "height",
    "ilosc": "quantity",
    "profil": "profile",
    "konfiguracja": "configuration",
    "otwieranie": "opening",
    "szyby": "glazing",
    "kolor_wewnetrzny": "color_inside",
    "kolor_od_srodka": "color_inside",
    "kolor_zewnetrzny": "color_outside",
    "kolor_z_zewnatrz": "color_outside",
    "cena": "price",
}
_ALLOWED_SOURCE_KINDS = frozenset(
    {
        "pdf_document",
        "salesperson_request",
        "application_knowledge",
        "approved_source",
        "deterministic_project_rule",
    }
)
_ALLOWED_ORIGINS = frozenset(
    {
        "explicit_request",
        "source_fact",
        "deterministic_rule",
        "model_inference",
    }
)
_FIELD_QUESTIONS = {
    "product_type": "Jakiego rodzaju produktu potrzebujesz?",
    "width": "Podaj proszę szerokość.",
    "height": "Podaj proszę wysokość.",
}
_UNIT_ALIASES = {
    "mm": "mm",
    "millimeter": "mm",
    "millimeters": "mm",
    "millimetre": "mm",
    "millimetres": "mm",
    "cm": "cm",
    "centimeter": "cm",
    "centimeters": "cm",
    "centimetre": "cm",
    "centimetres": "cm",
    "m": "m",
    "meter": "m",
    "meters": "m",
    "metre": "m",
    "metres": "m",
}
_DIMENSION_FACTORS = {"mm": Decimal("1"), "cm": Decimal("10"), "m": Decimal("1000")}
_VALUE_WITH_UNIT = re.compile(
    r"^\\s*([+-]?\\d+(?:[.,]\\d+)?)\\s*([a-zA-Z]+)?\\s*$"
)
_EXPLICIT_QUANTITY = re.compile(
    r"\\b(?:ilość|ilosc)\\s*[:=]?\\s*\\d+\\b"
    r"|\\b\\d+\\s*(?:szt\\.?|sztuk|sztuki|okien|okna|okno|drzwi)\\b"
    r"|\\b(?:potrzebuję|potrzebuje|chcę|chce)\\s+\\d+\\b"
    r"|\\b\\d+\\s*[x×]\\s*(?:okn|drzwi|window)",
    re.IGNORECASE,
)


def _nonempty(value: object, field_name: str, *, max_length: int = 500) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string.")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} must not be empty.")
    if len(normalized) > max_length:
        raise ValueError(f"{field_name} exceeds the maximum length.")
    return normalized


def _canonical_field(value: str) -> str:
    normalized = canonical_parameter_name(_nonempty(value, "field_name", max_length=80))
    normalized = _FIELD_ALIASES.get(normalized, normalized)
    if normalized not in _QUOTE_FIELDS:
        raise ValueError("Unsupported quote fact field.")
    return normalized


@dataclass(frozen=True)
class QuoteFactSource:
    """Safe, page/section-level provenance for a quote fact."""

    source_alias: str
    extraction_method: str
    page_number: int | None = None
    section: str | None = None
    source_kind: str = "pdf_document"

    def validate(self) -> None:
        alias = _nonempty(self.source_alias, "source_alias", max_length=255)
        if "/" in alias or "\\" in alias or ".." in alias:
            raise ValueError("source_alias must be a non-path alias.")
        _nonempty(self.extraction_method, "extraction_method", max_length=128)
        if self.source_kind not in _ALLOWED_SOURCE_KINDS:
            raise ValueError("Unsupported quote fact source kind.")
        if self.page_number is not None and (
            not isinstance(self.page_number, int)
            or isinstance(self.page_number, bool)
            or self.page_number < 1
        ):
            raise ValueError("page_number must be a positive 1-based integer.")
        if self.section is not None:
            _nonempty(self.section, "section", max_length=500)
        if self.page_number is None and not (
            isinstance(self.section, str) and self.section.strip()
        ):
            raise ValueError("Source provenance requires a page number or section.")

    def to_payload(self) -> dict[str, object]:
        self.validate()
        return {
            "source_alias": self.source_alias.strip(),
            "page_number": self.page_number,
            "section": self.section.strip() if self.section else None,
            "extraction_method": self.extraction_method.strip(),
            "source_kind": self.source_kind,
        }

    @classmethod
    def from_payload(cls, payload: object) -> "QuoteFactSource":
        if not isinstance(payload, dict):
            raise ValueError("Quote fact source must be a mapping.")
        source = cls(
            source_alias=payload.get("source_alias"),
            page_number=payload.get("page_number"),
            section=payload.get("section"),
            extraction_method=payload.get("extraction_method"),
            source_kind=payload.get("source_kind", "pdf_document"),
        )
        source.validate()
        return source


@dataclass(frozen=True)
class QuoteRuleEvidence:
    """Approved source or deterministic project rule for a derived decision."""

    rule_type: str
    rule_id: str
    source: QuoteFactSource
    approved: bool

    def validate(self) -> None:
        if self.rule_type not in {"pricing", "configuration"}:
            raise ValueError("Unsupported quote rule type.")
        _nonempty(self.rule_id, "rule_id", max_length=255)
        self.source.validate()
        if self.source.source_kind not in {
            "approved_source",
            "deterministic_project_rule",
        }:
            raise ValueError(
                "Quote rules require approved source material or a deterministic project rule."
            )
        if self.approved is not True:
            raise ValueError("Quote rule evidence is not approved.")

    def to_payload(self) -> dict[str, object]:
        self.validate()
        return {
            "rule_type": self.rule_type,
            "rule_id": self.rule_id.strip(),
            "source": self.source.to_payload(),
            "approved": True,
        }

    @classmethod
    def from_payload(cls, payload: object) -> "QuoteRuleEvidence":
        if not isinstance(payload, dict):
            raise ValueError("Quote rule evidence must be a mapping.")
        result = cls(
            rule_type=payload.get("rule_type"),
            rule_id=payload.get("rule_id"),
            source=QuoteFactSource.from_payload(payload.get("source")),
            approved=payload.get("approved") is True,
        )
        result.validate()
        return result


def _normalize_value(
    field_name: str,
    raw_value: str,
    unit: str | None,
) -> tuple[object, str | None]:
    raw = _nonempty(raw_value, "raw_value", max_length=2000)

    if field_name in {"width", "height"}:
        match = _VALUE_WITH_UNIT.fullmatch(raw)
        if match is None:
            raise ValueError(f"{field_name} must be a number with an optional length unit.")
        try:
            number = Decimal(match.group(1).replace(",", "."))
        except InvalidOperation as exc:
            raise ValueError(f"{field_name} is not a valid number.") from exc
        detected_unit = (unit or match.group(2) or "mm").strip().casefold()
        canonical_unit = _UNIT_ALIASES.get(detected_unit)
        if canonical_unit is None:
            raise ValueError(f"Unsupported length unit for {field_name}.")
        millimeters = number * _DIMENSION_FACTORS[canonical_unit]
        if millimeters != millimeters.to_integral_value():
            raise ValueError(f"{field_name} does not resolve to a whole millimeter.")
        return int(millimeters), "mm"

    if field_name == "quantity":
        match = _VALUE_WITH_UNIT.fullmatch(raw)
        if match is None:
            raise ValueError("quantity must be a whole number.")
        try:
            quantity = Decimal(match.group(1).replace(",", "."))
        except InvalidOperation as exc:
            raise ValueError("quantity is not a valid number.") from exc
        if quantity != quantity.to_integral_value():
            raise ValueError("quantity must be a whole number.")
        supplied_unit = (unit or match.group(2) or "piece").strip().casefold()
        if supplied_unit not in {"piece", "pieces", "pc", "pcs", "szt", "szt.", "sztuk", "sztuki"}:
            raise ValueError("Unsupported quantity unit.")
        return int(quantity), "piece"

    if field_name == "price":
        match = _VALUE_WITH_UNIT.fullmatch(raw)
        if match is None:
            raise ValueError("price must be a decimal amount with a currency unit.")
        try:
            amount = Decimal(match.group(1).replace(",", "."))
        except InvalidOperation as exc:
            raise ValueError("price is not a valid decimal amount.") from exc
        currency = (unit or match.group(2) or "").strip().upper()
        if currency not in {"PLN", "EUR", "USD", "GBP", "CHF", "CZK"}:
            raise ValueError("price requires a recognized explicit currency unit.")
        if amount < 0:
            raise ValueError("price cannot be negative.")
        return amount, currency

    value = " ".join(raw.split())
    normalized = value.casefold()
    if field_name == "product_type":
        aliases = {
            "okno": "window",
            "okna": "window",
            "okien": "window",
            "window": "window",
            "drzwi": "door",
            "door": "door",
            "drzwi balkonowe": "balcony_door",
            "balcony door": "balcony_door",
            "hs": "sliding_door",
            "h.s.": "sliding_door",
            "przesuwne": "sliding_door",
            "sliding door": "sliding_door",
        }
        normalized = aliases.get(normalized, normalized)
    elif field_name == "configuration":
        aliases = {
            "jednoskrzydłowe": "single_leaf",
            "jednoskrzydlowe": "single_leaf",
            "dwuskrzydłowe": "double_leaf",
            "dwuskrzydlowe": "double_leaf",
            "fix": "fixed",
            "nieotwierane": "fixed",
        }
        normalized = aliases.get(normalized, normalized)
    elif field_name == "glazing":
        aliases = {
            "dwuszybowe": "double",
            "2 szyb": "double",
            "double": "double",
            "trzyszybowe": "triple",
            "3 szyb": "triple",
            "triple": "triple",
        }
        normalized = aliases.get(normalized, normalized)
    elif field_name in {"color_inside", "color_outside"}:
        aliases = {
            "biały": "white",
            "białe": "white",
            "biała": "white",
            "white": "white",
            "antracyt": "anthracite",
            "anthracite": "anthracite",
            "czarny": "black",
            "black": "black",
            "brąz": "brown",
            "brown": "brown",
        }
        normalized = aliases.get(normalized, normalized)
    elif field_name == "profile":
        # Preserve the project's catalog-style profile identifiers.
        normalized = value.upper()
    elif field_name == "opening":
        normalized = value.upper() if re.fullmatch(r"[A-Za-z0-9_ -]+", value) else value
    return normalized, None


@dataclass(frozen=True)
class QuoteFact:
    """A typed value tied to page/section provenance, with no runtime metadata."""

    field_name: str
    raw_value: str
    source: QuoteFactSource
    confidence: float
    origin: str = "source_fact"
    unit: str | None = None
    rule_evidence: QuoteRuleEvidence | None = None
    evidence_text: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "field_name", _canonical_field(self.field_name))

    def validate(self) -> None:
        _nonempty(self.raw_value, "raw_value", max_length=2000)
        self.source.validate()
        if (
            not isinstance(self.confidence, (int, float))
            or isinstance(self.confidence, bool)
            or not math.isfinite(float(self.confidence))
            or not 0.0 <= float(self.confidence) <= 1.0
        ):
            raise ValueError("confidence must be between 0 and 1.")
        if self.origin not in _ALLOWED_ORIGINS:
            raise ValueError("Unsupported quote fact origin.")
        if self.unit is not None:
            _nonempty(self.unit, "unit", max_length=32)
        if self.evidence_text is not None:
            _nonempty(self.evidence_text, "evidence_text", max_length=4000)
        if self.rule_evidence is not None:
            self.rule_evidence.validate()

    @property
    def normalized_value(self) -> object:
        value, _ = _normalize_value(self.field_name, self.raw_value, self.unit)
        return value

    @property
    def normalized_unit(self) -> str | None:
        _, normalized_unit = _normalize_value(self.field_name, self.raw_value, self.unit)
        return normalized_unit

    def to_payload(self) -> dict[str, object]:
        self.validate()
        payload: dict[str, object] = {
            "field_name": self.field_name,
            "raw_value": self.raw_value.strip(),
            "source": self.source.to_payload(),
            "confidence": float(self.confidence),
            "origin": self.origin,
            "unit": self.unit.strip() if self.unit else None,
            "evidence_text": self.evidence_text.strip() if self.evidence_text else None,
        }
        if self.rule_evidence is not None:
            payload["rule_evidence"] = self.rule_evidence.to_payload()
        try:
            normalized = self.normalized_value
            payload["normalized_value"] = str(normalized) if isinstance(normalized, Decimal) else normalized
            payload["normalized_unit"] = self.normalized_unit
        except ValueError:
            payload["normalization_error"] = "invalid_value"
        return payload

    @classmethod
    def from_payload(cls, payload: object) -> "QuoteFact":
        if not isinstance(payload, dict):
            raise ValueError("Quote fact must be a mapping.")
        result = cls(
            field_name=payload.get("field_name"),
            raw_value=payload.get("raw_value"),
            source=QuoteFactSource.from_payload(payload.get("source")),
            confidence=payload.get("confidence"),
            origin=payload.get("origin", "source_fact"),
            unit=payload.get("unit"),
            rule_evidence=(
                QuoteRuleEvidence.from_payload(payload["rule_evidence"])
                if payload.get("rule_evidence") is not None
                else None
            ),
            evidence_text=payload.get("evidence_text"),
        )
        result.validate()
        # Ignore caller-supplied normalized fields. Normalization is recomputed locally.
        return result


@dataclass(frozen=True)
class QuoteFactConflict:
    code: str
    field_name: str
    message: str
    sources: tuple[QuoteFactSource, ...] = ()
    values: tuple[str, ...] = ()

    def to_payload(self) -> dict[str, object]:
        return {
            "code": self.code,
            "field_name": self.field_name,
            "message": self.message,
            "sources": [source.to_payload() for source in self.sources],
            "values": list(self.values),
        }


@dataclass(frozen=True)
class QuoteFactsValidationResult:
    """Fail-closed validation result suitable for review or execution gating."""

    facts: tuple[QuoteFact, ...]
    normalized_values: Mapping[str, object]
    missing_fields: tuple[str, ...]
    conflicts: tuple[QuoteFactConflict, ...]
    questions: tuple[str, ...]

    @property
    def can_execute(self) -> bool:
        return not self.missing_fields and not self.conflicts

    @property
    def requires_manual_review(self) -> bool:
        return not self.can_execute

    def to_payload(self) -> dict[str, object]:
        normalized_values = {
            key: (str(value) if isinstance(value, Decimal) else value)
            for key, value in self.normalized_values.items()
        }
        return {
            "version": QUOTE_FACTS_VERSION,
            "can_execute": self.can_execute,
            "requires_manual_review": self.requires_manual_review,
            "normalized_values": normalized_values,
            "missing_fields": list(self.missing_fields),
            "conflicts": [conflict.to_payload() for conflict in self.conflicts],
            "questions": list(self.questions),
            "facts": [fact.to_payload() for fact in self.facts],
        }

    def to_offer_context(self, raw_request: str) -> OfferContext:
        if not self.can_execute:
            raise ValueError("Cannot create an offer context from invalid quote facts.")
        base = OfferContextParser().parse(raw_request)
        values = self.normalized_values
        profile_source = (
            ProfileSelectionSource.EXPLICIT
            if "profile" in values
            else base.profile_source
        )
        opening = str(values.get("opening", base.opening)) if (
            values.get("opening", base.opening) is not None
        ) else None
        openings = (
            (opening,) if opening is not None and "opening" in values else base.openings
        )
        return OfferContext(
            raw_request=raw_request,
            width=int(values["width"]) if "width" in values else base.width,
            height=int(values["height"]) if "height" in values else base.height,
            quantity=int(values["quantity"]) if "quantity" in values else base.quantity,
            product_type=str(values["product_type"]) if "product_type" in values else base.product_type,
            profile=str(values["profile"]) if "profile" in values else base.profile,
            profile_source=profile_source,
            configuration=str(values["configuration"]) if "configuration" in values else base.configuration,
            opening=opening,
            openings=openings,
            color_inside=str(values["color_inside"]) if "color_inside" in values else base.color_inside,
            color_outside=str(values["color_outside"]) if "color_outside" in values else base.color_outside,
            glazing=str(values["glazing"]) if "glazing" in values else base.glazing,
            missing_fields=(),
            conflicts=(),
        )


class QuoteFactValidator:
    """Deterministic validation; it never invents prices or product rules."""

    REQUIRED_FIELDS = OfferContextValidator.REQUIRED_FIELDS

    def validate(
        self,
        facts: Iterable[QuoteFact],
        *,
        request_conflicts: Iterable[str] = (),
        known_sources: Mapping[str, object] | None = None,
        approved_rules: Mapping[str, QuoteRuleEvidence] | Iterable[QuoteRuleEvidence] = (),
    ) -> QuoteFactsValidationResult:
        fact_tuple = tuple(facts)
        conflicts: list[QuoteFactConflict] = []
        grouped: dict[str, list[tuple[QuoteFact, object]]] = {}
        if isinstance(approved_rules, Mapping):
            rule_registry = dict(approved_rules)
        else:
            rule_registry = {
                rule.rule_id: rule
                for rule in approved_rules
                if isinstance(rule, QuoteRuleEvidence)
            }

        for fact in fact_tuple:
            try:
                fact.validate()
                normalized = fact.normalized_value
            except (TypeError, ValueError) as exc:
                conflicts.append(
                    QuoteFactConflict(
                        code="invalid_quote_fact",
                        field_name=getattr(fact, "field_name", "unknown"),
                        message=str(exc),
                        sources=(fact.source,) if isinstance(fact, QuoteFact) else (),
                    )
                )
                continue

            source_error = self._validate_fact_source(fact, known_sources)
            if source_error is not None:
                conflicts.append(
                    QuoteFactConflict(
                        code="unverified_source_provenance",
                        field_name=fact.field_name,
                        message=source_error,
                        sources=(fact.source,),
                        values=(str(normalized),),
                    )
                )

            requires_rule = (
                fact.field_name == "price" and fact.origin == "model_inference"
            ) or (
                fact.field_name == "configuration"
                and fact.origin in {"model_inference", "deterministic_rule"}
            ) or (
                fact.field_name == "price"
                and fact.origin == "deterministic_rule"
            )
            if requires_rule:
                expected_rule = "pricing" if fact.field_name == "price" else "configuration"
                evidence = fact.rule_evidence
                try:
                    if evidence is None or evidence.rule_type != expected_rule:
                        raise ValueError("matching approved rule evidence is missing")
                    evidence.validate()
                    trusted = rule_registry.get(evidence.rule_id)
                    if trusted is None or trusted != evidence:
                        raise ValueError("rule is not present in the trusted approved-rule registry")
                except (TypeError, ValueError) as exc:
                    code = "unsourced_pricing_rule" if fact.field_name == "price" else "unsourced_configuration_rule"
                    conflicts.append(
                        QuoteFactConflict(
                            code=code,
                            field_name=fact.field_name,
                            message=(
                                f"Derived {fact.field_name} is blocked without "
                                f"trusted approved {expected_rule} evidence: {exc}."
                            ),
                            sources=(fact.source,),
                            values=(str(normalized),),
                        )
                    )

            grouped.setdefault(fact.field_name, []).append((fact, normalized))

        normalized_values: dict[str, object] = {}
        for field_name, entries in grouped.items():
            first = entries[0][1]
            comparison = _comparable(first)
            different = any(_comparable(value) != comparison for _, value in entries[1:])
            if different:
                conflicts.append(
                    QuoteFactConflict(
                        code=f"conflicting_{field_name}",
                        field_name=field_name,
                        message=f"Conflicting values for '{field_name}' were found across sources.",
                        sources=tuple(fact.source for fact, _ in entries),
                        values=tuple(_display_value(value) for _, value in entries),
                    )
                )
            else:
                normalized_values[field_name] = first

        missing_fields = tuple(
            field_name for field_name in self.REQUIRED_FIELDS
            if field_name not in normalized_values
        )
        unique_conflicts: list[QuoteFactConflict] = []
        seen_conflicts: set[tuple[str, str, tuple[str, ...]]] = set()
        for conflict in conflicts:
            identity = (conflict.code, conflict.field_name, conflict.values)
            if identity not in seen_conflicts:
                seen_conflicts.add(identity)
                unique_conflicts.append(conflict)

        for request_conflict in request_conflicts:
            unique_conflicts.append(
                QuoteFactConflict(
                    code="request_requires_manual_review",
                    field_name="offer_request",
                    message=str(request_conflict),
                )
            )

        questions = tuple(
            _FIELD_QUESTIONS[field_name]
            for field_name in missing_fields
            if field_name in _FIELD_QUESTIONS
        )
        if unique_conflicts:
            questions += ("Wykryto sprzeczne lub niezatwierdzone dane. Wymagana jest ręczna weryfikacja przed działaniem w WindowHub.",)

        return QuoteFactsValidationResult(
            facts=fact_tuple,
            normalized_values=normalized_values,
            missing_fields=missing_fields,
            conflicts=tuple(unique_conflicts),
            questions=tuple(dict.fromkeys(questions)),
        )

    def validate_payload(
        self,
        payload: object,
        *,
        request_message: str | None = None,
        pdf_sources: Mapping[str, object] | None = None,
        approved_rules: Mapping[str, QuoteRuleEvidence] | Iterable[QuoteRuleEvidence] = (),
    ) -> QuoteFactsValidationResult:
        """Parse a narrow, versioned envelope; ignore unrelated metadata by design."""
        try:
            if not isinstance(payload, dict):
                raise ValueError("quote_facts must be a mapping.")
            if payload.get("version") != QUOTE_FACTS_VERSION:
                raise ValueError("Unsupported quote facts version.")
            raw_facts = payload.get("facts")
            if not isinstance(raw_facts, list):
                raise ValueError("quote_facts.facts must be a list.")
            if len(raw_facts) > 64:
                raise ValueError("quote_facts contains too many facts.")
            facts = [QuoteFact.from_payload(item) for item in raw_facts]
        except (TypeError, ValueError) as exc:
            conflict = QuoteFactConflict(
                code="invalid_quote_facts_payload",
                field_name="quote_facts",
                message=str(exc),
            )
            return QuoteFactsValidationResult(
                facts=(),
                normalized_values={},
                missing_fields=tuple(self.REQUIRED_FIELDS),
                conflicts=(conflict,),
                questions=tuple(
                    _FIELD_QUESTIONS[field_name]
                    for field_name in self.REQUIRED_FIELDS
                    if field_name in _FIELD_QUESTIONS
                ) + ("Dane oferty mają nieprawidłowy format. Wymagana jest ręczna weryfikacja.",),
            )

        parser_conflicts: tuple[str, ...] = ()
        request_facts: tuple[QuoteFact, ...] = ()
        if isinstance(request_message, str) and request_message.strip():
            request_context = OfferContextParser().parse(request_message)
            parser_conflicts = tuple(request_context.conflicts)
            request_facts = self._facts_from_request_context(
                request_context,
            )
        return self.validate(
            (*facts, *request_facts),
            request_conflicts=parser_conflicts,
            known_sources=pdf_sources,
            approved_rules=approved_rules,
        )

    @staticmethod
    def _validate_fact_source(
        fact: QuoteFact,
        known_sources: Mapping[str, object] | None,
    ) -> str | None:
        if fact.source.source_kind != "pdf_document":
            return None

        if known_sources is None:
            return "PDF fact has no trusted in-process PDF extraction registry."
        extraction = known_sources.get(fact.source.source_alias)
        if extraction is None:
            return "PDF source alias is not present in the trusted extraction registry."

        from app.agent.adapters.pdf_document_adapter import PdfDocumentExtraction

        if not isinstance(extraction, PdfDocumentExtraction):
            return "PDF source registry entry is not a trusted PdfDocumentExtraction object."
        if extraction.source_alias != fact.source.source_alias:
            return "PDF source alias does not match the extraction result."
        if fact.source.page_number is None:
            return "PDF fact provenance must identify a 1-based page number."
        page = next(
            (
                item for item in extraction.pages
                if item.page_number == fact.source.page_number
            ),
            None,
        )
        if page is None:
            return "PDF fact page number is outside the extracted source."
        if page.extraction_method != fact.source.extraction_method:
            return "PDF extraction method does not match the extracted page."
        if page.needs_ocr:
            return "PDF fact cannot be accepted from a page that still requires OCR."
        if not fact.evidence_text:
            return "PDF fact must include a verbatim evidence_text excerpt."
        normalize_space = lambda value: " ".join(value.casefold().split())
        normalized_page = normalize_space(page.text)
        normalized_evidence = normalize_space(fact.evidence_text)
        normalized_value = normalize_space(fact.raw_value)
        if normalized_evidence not in normalized_page:
            return "PDF fact evidence_text is not present in the trusted extracted page."
        if normalized_value not in normalized_evidence:
            return "PDF fact raw_value is not present in its evidence_text excerpt."
        return None

    @staticmethod
    def envelope(facts: Iterable[QuoteFact]) -> dict[str, object]:
        return {
            "version": QUOTE_FACTS_VERSION,
            "facts": [fact.to_payload() for fact in facts],
        }

    @staticmethod
    def _facts_from_request_context(context: OfferContext) -> tuple[QuoteFact, ...]:
        source = QuoteFactSource(
            source_alias="salesperson-request",
            section="message",
            extraction_method="OfferContextParser",
            source_kind="salesperson_request",
        )
        values: list[tuple[str, object, str | None]] = [
            ("product_type", context.product_type, None),
            ("width", context.width, "mm"),
            ("height", context.height, "mm"),
            ("configuration", context.configuration, None),
            ("opening", context.opening, None),
            ("glazing", context.glazing, None),
            ("color_inside", context.color_inside, None),
            ("color_outside", context.color_outside, None),
        ]
        if context.profile is not None and context.profile_source == ProfileSelectionSource.EXPLICIT:
            values.append(("profile", context.profile, None))
        if _EXPLICIT_QUANTITY.search(context.raw_request):
            values.append(("quantity", context.quantity, "piece"))

        facts = []
        for field_name, value, unit in values:
            if value is None:
                continue
            raw_value = f"{value} {unit}" if unit in {"mm", "piece"} else str(value)
            facts.append(
                QuoteFact(
                    field_name=field_name,
                    raw_value=raw_value,
                    source=source,
                    confidence=0.99,
                    origin="explicit_request",
                    unit=unit,
                )
            )
        return tuple(facts)


def _comparable(value: object) -> object:
    if isinstance(value, Decimal):
        return value.normalize()
    if isinstance(value, str):
        return value.casefold().strip()
    return value


def _display_value(value: object) -> str:
    if isinstance(value, Decimal):
        return str(value)
    return str(value)
