from __future__ import annotations

from collections.abc import Iterable

from app.quote_orchestrator import IssueSeverity, PreflightIssue, QuoteItem
from app.wh.runtime.construction_project import ConstructionProject


class ConstructionPreflightValidator:
    """Validate construction data before it reaches the semantic executor.

    This validator checks data integrity and known mapper boundaries. It does
    not invent technical limits or silently change a customer's construction.
    """

    def __call__(self, item: QuoteItem) -> Iterable[PreflightIssue]:
        project = item.payload
        if not isinstance(project, ConstructionProject):
            yield PreflightIssue(
                item_id=item.item_id,
                severity=IssueSeverity.FATAL,
                code="INVALID_PAYLOAD",
                message="Quote item payload is not a ConstructionProject.",
            )
            return

        schema = project.schema

        if schema.width <= 0 or schema.height <= 0:
            yield PreflightIssue(
                item_id=item.item_id,
                severity=IssueSeverity.BLOCKING,
                code="INVALID_DIMENSIONS",
                message="Construction width and height must be greater than zero.",
            )

        if not schema.segments:
            yield PreflightIssue(
                item_id=item.item_id,
                severity=IssueSeverity.BLOCKING,
                code="NO_SEGMENTS",
                message="Construction has no segments to execute.",
            )
            return

        # The current canonical mapper has explicit LEFT/RIGHT cell targets.
        # Do not let a third segment overwrite the RIGHT element silently.
        if len(schema.segments) > 2:
            yield PreflightIssue(
                item_id=item.item_id,
                severity=IssueSeverity.BLOCKING,
                code="UNSUPPORTED_CELL_COUNT",
                message="Current semantic mapper supports at most two cells.",
            )

        for index, segment in enumerate(schema.segments, start=1):
            if segment.width_ratio <= 0 or segment.height_ratio <= 0:
                yield PreflightIssue(
                    item_id=item.item_id,
                    severity=IssueSeverity.BLOCKING,
                    code="INVALID_SEGMENT_RATIO",
                    message=f"Segment {index} has non-positive width/height ratio.",
                )

            if not getattr(segment, "opening", None):
                yield PreflightIssue(
                    item_id=item.item_id,
                    severity=IssueSeverity.BLOCKING,
                    code="MISSING_OPENING",
                    message=f"Segment {index} has no opening type.",
                )
