"""Top Trans live-acceptance preflight: explainable intent, no invented values.

Specific controlled two-window acceptance fixture, not a general NLU engine.
Never emits WindowHub action grants. In particular an unknown dimension
cannot become the default 1000 mm dimension present in some UI dialogs.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
import json
from pathlib import Path
from typing import Literal


@dataclass(frozen=True)
class WindowSpec:
    position: int
    quantity: int
    leaves: int
    colour_outside: str | None
    colour_inside: str | None
    glazing_panes: int | None
    width_mm: int | None
    height_mm: int | None
    opening: str | None


@dataclass(frozen=True)
class TopTransAcceptance:
    customer: str
    positions: tuple[WindowSpec, ...]
    hide_prices: tuple[str, ...]
    show_construction_price: bool
    status: Literal["REVIEW_ONLY", "READY_FOR_LIVE_ENTRY"]
    missing: tuple[str, ...]
    assumptions_to_confirm: tuple[str, ...]
    live_gui_actions_authorized: bool = False
    save_authorized: bool = False
    sent_to_customer: bool = False

    def serialize(self) -> str:
        return json.dumps(asdict(self), indent=2, ensure_ascii=False)


def top_trans_acceptance(
    *, widths_mm: tuple[int | None, int | None] = (None, None),
    heights_mm: tuple[int | None, int | None] = (None, None),
    opening: tuple[str | None, str | None] = (None, None),
    anthracite_side: Literal["outside", "inside"] | None = None,
    confirm_first_glazing: int | None = None,
) -> TopTransAcceptance:
    """Never infer missing information or quietly grant GUI execution.

    Default two-pane glazing is an explicit *proposal*, not a property in
    the customer request for position 1.
    """
    for value in widths_mm + heights_mm:
        if value is not None and (type(value) is not int or not 300 <= value <= 5000):
            raise ValueError("dimension_not_validated_for_acceptance")
    if confirm_first_glazing not in (None, 2, 3):
        raise ValueError("unsupported_first_glazing")
    if anthracite_side not in (None, "outside", "inside"):
        raise ValueError("invalid_anthracite_side")
    for direction in opening:
        if direction is not None and direction not in (
            "left", "right", "main_left", "main_right"
        ):
            raise ValueError("unsupported_opening_direction")

    missing: list[str] = []
    for i in (0, 1):
        if widths_mm[i] is None:
            missing.append(f"position_{i + 1}:width_mm")
        if heights_mm[i] is None:
            missing.append(f"position_{i + 1}:height_mm")
        if opening[i] is None:
            missing.append(f"position_{i + 1}:opening_direction")
    if anthracite_side is None:
        missing.append("position_2:anthracite_side")
    if confirm_first_glazing is None:
        missing.append("position_1:glazing_panes")
    second_inside = (
        "biały" if anthracite_side == "outside" else
        "antracyt struktura 701605" if anthracite_side == "inside" else None
    )
    second_outside = (
        "antracyt struktura 701605" if anthracite_side == "outside" else
        "biały" if anthracite_side == "inside" else None
    )
    return TopTransAcceptance(
        customer="Top Trans",
        positions=(
            WindowSpec(
                1, 1, 1, "biały", "biały", confirm_first_glazing,
                widths_mm[0], heights_mm[0], opening[0],
            ),
            WindowSpec(
                2, 1, 2, second_outside, second_inside, 2,
                widths_mm[1], heights_mm[1], opening[1],
            ),
        ),
        hide_prices=("montaż", "demontaż", "wykończenie"),
        show_construction_price=True,
        status="REVIEW_ONLY",
        missing=tuple(missing),
        assumptions_to_confirm=(
            "position_1:2_panes_as_default_proposal"
            if confirm_first_glazing is None else
            "position_1:glazing_confirmed",
            "position_2:anthracite_outside_white_inside_proposed"
            if anthracite_side is None else
            "position_2:anthracite_side_confirmed",
            "profile_system_not_selected",
            "windowhub_customer_identity_must_be_verified",
            "native_windowhub_position_editing_not_yet_connected",
        ),
    )


def top_trans_report() -> str:
    mission = top_trans_acceptance()
    return (
        "NAVIMIND_TOP_TRANS_PREFLIGHT=REVIEW_ONLY\n"
        "CUSTOMER=Top Trans\n"
        "POSITIONS=2\n"
        "WINDOWS_TOTAL=2\n"
        "PRICES_TO_HIDE=montaz,demontaz,wykonczenie\n"
        "CONSTRUCTION_PRICE_VISIBLE=True\n"
        "MISSING=" + ",".join(mission.missing) + "\n"
        "REAL_WINDOWHUB_ACTIONS=0\n"
        "NATIVE_V2_EXECUTOR_CONNECTED=False\n"
        "OFFER_NOT_SAVED=True\n"
    )
