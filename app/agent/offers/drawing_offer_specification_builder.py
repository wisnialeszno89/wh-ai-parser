"""Build a multi-window offer specification only after explicit human review.

This module is a local data-preparation boundary. It does not create a WindowHub
task, observe a GUI, save an offer, or send a request to any external service.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from app.agent.offers.drawing_position_extractor import DrawingPositionExtractionResult
from app.wh.domain.offer.offer_specification import OfferSpecification
from app.wh.domain.offer.window_requirement import WindowRequirement


@dataclass(frozen=True)
class ReviewedDrawingPosition:
    """Values a person checked against the original drawing for one position."""

    position_number: int
    width_mm: int
    height_mm: int
    quantity: int
    human_confirmed: bool = False

    def validate(self) -> None:
        if (
            not isinstance(self.position_number, int)
            or isinstance(self.position_number, bool)
            or self.position_number < 1
        ):
            raise ValueError("position_number must be a positive integer.")
        if (
            not isinstance(self.width_mm, int)
            or isinstance(self.width_mm, bool)
            or not 200 <= self.width_mm <= 6000
        ):
            raise ValueError("width_mm must be a whole dimension from 200 to 6000 mm.")
        if (
            not isinstance(self.height_mm, int)
            or isinstance(self.height_mm, bool)
            or not 200 <= self.height_mm <= 6000
        ):
            raise ValueError("height_mm must be a whole dimension from 200 to 6000 mm.")
        if (
            not isinstance(self.quantity, int)
            or isinstance(self.quantity, bool)
            or not 1 <= self.quantity <= 1000
        ):
            raise ValueError("quantity must be a whole number from 1 to 1000.")
        if self.human_confirmed is not True:
            raise ValueError(
                f"Position {self.position_number} has not been explicitly confirmed by a person."
            )

    def to_payload(self) -> dict[str, object]:
        self.validate()
        return {
            "position_number": self.position_number,
            "width_mm": self.width_mm,
            "height_mm": self.height_mm,
            "quantity": self.quantity,
            "human_confirmed": True,
        }


@dataclass(frozen=True)
class DrawingOfferSpecificationResult:
    """A multi-window specification prepared from explicitly reviewed values."""

    source_alias: str
    page_number: int
    specification: OfferSpecification
    positions: tuple[ReviewedDrawingPosition, ...]

    @property
    def total_quantity(self) -> int:
        return sum(position.quantity for position in self.positions)

    def to_payload(self) -> dict[str, object]:
        """Serialize only reviewed field values; never claim a live offer exists."""
        return {
            "status": "human_reviewed_specification_prepared",
            "source_alias": self.source_alias,
            "page_number": self.page_number,
            "position_count": len(self.positions),
            "total_quantity": self.total_quantity,
            "positions": [position.to_payload() for position in self.positions],
            "offer_specification": {
                "customer_name": self.specification.customer_name,
                "language": self.specification.language,
                "installation": self.specification.installation,
                "transport": self.specification.transport,
                "notes": self.specification.notes,
                "windows": [
                    {
                        "width": window.width,
                        "height": window.height,
                        "quantity": window.quantity,
                    }
                    for window in self.specification.windows
                ],
            },
            "review_confirmed": True,
            "windowhub_task_created": False,
            "windowhub_actions_executed": 0,
            "offer_saved": False,
            "offer_submitted": False,
        }


class DrawingOfferSpecificationBuilder:
    """Map reviewed OCR candidates to the existing multi-window domain model.

    The caller must explicitly confirm both the position set and every reviewed
    field value after viewing the original source. Values may be corrected by the
    reviewer. This builder returns a local domain object only; the existing
    single-window PDF task workflow is intentionally not invoked here.
    """

    def build(
        self,
        extraction: DrawingPositionExtractionResult,
        *,
        reviewed_positions: Iterable[ReviewedDrawingPosition],
        expected_position_numbers: Iterable[int],
        review_confirmed: bool,
        customer_name: str = "",
        language: str = "",
        installation: bool = False,
        transport: bool = False,
        notes: str = "",
    ) -> DrawingOfferSpecificationResult:
        if not isinstance(extraction, DrawingPositionExtractionResult):
            raise TypeError(
                "extraction must be a DrawingPositionExtractionResult."
            )
        if not extraction.source_alias.strip() or extraction.page_number < 1:
            raise ValueError("A valid source alias and page number are required.")
        if review_confirmed is not True:
            raise ValueError(
                "The position set must be explicitly confirmed after visual review."
            )
        if not isinstance(customer_name, str) or len(customer_name) > 250:
            raise ValueError("customer_name must be a string of at most 250 characters.")
        if not isinstance(language, str) or len(language) > 16:
            raise ValueError("language must be a string of at most 16 characters.")
        if not isinstance(notes, str) or len(notes) > 4000:
            raise ValueError("notes must be a string of at most 4000 characters.")
        if not isinstance(installation, bool) or not isinstance(transport, bool):
            raise ValueError("installation and transport must be boolean values.")

        candidates = tuple(extraction.positions)
        candidate_numbers = [item.position_number for item in candidates]
        if not candidates or len(candidate_numbers) != len(set(candidate_numbers)):
            raise ValueError("The OCR candidate set is empty or contains duplicate positions.")

        expected_numbers = tuple(expected_position_numbers)
        if (
            not expected_numbers
            or any(
                not isinstance(number, int) or isinstance(number, bool) or number < 1
                for number in expected_numbers
            )
            or len(expected_numbers) != len(set(expected_numbers))
        ):
            raise ValueError("expected_position_numbers must be unique positive integers.")

        candidate_set = set(candidate_numbers)
        if set(expected_numbers) != candidate_set:
            raise ValueError(
                "The visually confirmed position list does not match the OCR candidate list."
            )

        reviewed = tuple(reviewed_positions)
        reviewed_numbers = [item.position_number for item in reviewed]
        if (
            len(reviewed_numbers) != len(set(reviewed_numbers))
            or set(reviewed_numbers) != candidate_set
        ):
            raise ValueError(
                "Every OCR position must have exactly one reviewed position value."
            )

        for position in reviewed:
            if not isinstance(position, ReviewedDrawingPosition):
                raise TypeError("All reviewed positions must be ReviewedDrawingPosition values.")
            position.validate()

        reviewed = tuple(sorted(reviewed, key=lambda item: item.position_number))
        specification = OfferSpecification(
            customer_name=customer_name.strip(),
            language=language.strip(),
            windows=[
                WindowRequirement(
                    width=position.width_mm,
                    height=position.height_mm,
                    quantity=position.quantity,
                )
                for position in reviewed
            ],
            installation=installation,
            transport=transport,
            notes=notes.strip(),
        )
        return DrawingOfferSpecificationResult(
            source_alias=extraction.source_alias,
            page_number=extraction.page_number,
            specification=specification,
            positions=reviewed,
        )
