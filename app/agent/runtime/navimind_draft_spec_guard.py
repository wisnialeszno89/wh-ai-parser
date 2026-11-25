"""Pure, evidence-bound text-entry policy for an unsaved WindowHub offer.

Model-generated values are proposals. Only exact, unambiguous customer/user
specification evidence may authorize filling mapped geometric/quantity fields.
This policy never executes input, saves documents or invents product options.
"""
from __future__ import annotations

from dataclasses import dataclass
import re

_SIZE = re.compile(
    r"(?<![\d.,])([1-9][0-9]{2,3})\s*[x×]\s*([1-9][0-9]{2,3})(?![\d.,])"
    r"(?:\s*mm)?", re.IGNORECASE,
)
_QUANTITY = re.compile(
    r"(?<!\w)([1-9][0-9]?)\s*(?:szt\.?|stk\.?|stück|okn(?:a|o|ien)|fenster)"
    r"(?!\w)", re.IGNORECASE,
)


@dataclass(frozen=True)
class DraftSpecEvidence:
    sizes: tuple[tuple[int, int], ...]
    quantity: int | None
    has_multiple_sizes: bool

    @property
    def single_size(self) -> tuple[int, int] | None:
        return self.sizes[0] if len(self.sizes) == 1 else None


def extract_draft_spec(goal: str, consented_evidence: str = "") -> DraftSpecEvidence:
    if not isinstance(goal, str) or not isinstance(consented_evidence, str):
        raise ValueError("draft_spec_evidence_invalid")
    # The two trusted sources are the human chat turn and explicitly approved
    # document material. Do not use the model reply or UI arbitrary values.
    text = goal + "\n" + consented_evidence
    sizes = sorted(set(
        (int(w), int(h)) for w, h in _SIZE.findall(text)
        if 200 <= int(w) <= 5000 and 200 <= int(h) <= 5000
    ))
    quantities = {int(q) for q in _QUANTITY.findall(text)}
    unique_qty = next(iter(quantities)) if len(quantities) == 1 else None
    return DraftSpecEvidence(
        sizes=tuple(sizes), quantity=unique_qty,
        has_multiple_sizes=len(sizes) > 1,
    )


def validate_draft_text_entry(
    *, goal: str, consented_evidence: str,
    field_name: str, proposed_value: str,
) -> tuple[bool, str]:
    if not isinstance(proposed_value, str) or not proposed_value.strip():
        return False, "draft_value_missing"
    data = extract_draft_spec(goal, consented_evidence)
    requested = proposed_value.strip()
    dims = data.single_size
    if field_name in {"width_1", "height_1"}:
        if dims is None:
            return False, "draft_dimensions_missing_or_ambiguous"
        desired = dims[0 if field_name == "width_1" else 1]
        return (
            (True, "matches_exact_human_or_approved_pdf_dimensions")
            if requested == str(desired)
            else (False, "draft_dimensions_not_supported_by_source")
        )
    if field_name == "quantity_input":
        if data.has_multiple_sizes or data.quantity is None:
            return False, "draft_quantity_missing_or_ambiguous"
        return (
            (True, "matches_requested_quantity")
            if requested == str(data.quantity)
            else (False, "draft_quantity_not_supported_by_source")
        )
    if field_name == "description_input":
        normalized = " ".join(requested.casefold().split())
        if len(normalized) < 4 or len(normalized) > 160:
            return False, "draft_description_length_unverified"
        # Description may be copied, not hallucinated. Source instructions
        # still cannot authorize native actions or escaping the scope.
        sources = " ".join((goal + " " + consented_evidence).casefold().split())
        if normalized not in sources:
            return False, "draft_description_not_present_in_source"
        return True, "verbatim_source_description"
    return False, "draft_field_not_covered_by_business_evidence"
