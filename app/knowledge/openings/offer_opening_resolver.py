from app.knowledge.openings.opening_knowledge_resolver import (
    OpeningKnowledgeResolver,
)
from app.knowledge.openings.opening_resolution import (
    OpeningResolution,
    OpeningResolutionStatus,
)


class OfferOpeningResolver:
    """
    Resolve a technical opening mentioned in a raw
    quotation request using Knowledge.

    Generic tilt-and-turn descriptions are treated as
    ambiguous because they do not contain a direction.
    """

    GENERIC_TILT_TURN_ALIASES = (
        "dreh-kipp",
        "dreh kipp",
        "tilt and turn",
        "tilt-turn",
        "tilt turn",
        "uchylno-rozwierne",
    )

    def __init__(
        self,
        resolver: OpeningKnowledgeResolver | None = None,
    ):
        self.resolver = (
            resolver or OpeningKnowledgeResolver()
        )

    def resolve_result(
        self,
        request: str,
    ) -> OpeningResolution:

        repository = self.resolver.repository

        matches = repository.find_codes_in_text(
            request
        )

        normalized_request = request.casefold()

        has_generic_tilt_turn = any(
            alias in normalized_request
            for alias in self.GENERIC_TILT_TURN_ALIASES
        )

        if has_generic_tilt_turn and not matches:
            return OpeningResolution(
                status=(
                    OpeningResolutionStatus.AMBIGUOUS
                ),
            )

        if len(matches) == 1:
            return OpeningResolution(
                status=(
                    OpeningResolutionStatus.RESOLVED
                ),
                code=matches[0],
                matches=tuple(matches),
            )

        if len(matches) > 1:
            return OpeningResolution(
                status=(
                    OpeningResolutionStatus.AMBIGUOUS
                ),
                matches=tuple(matches),
            )

        return OpeningResolution(
            status=OpeningResolutionStatus.NOT_FOUND,
        )

    def resolve_all(
        self,
        request: str,
    ) -> tuple[str, ...]:
        matches = (
            self.resolver.repository
            .find_occurrences_in_text(request)
        )

        return tuple(
            code
            for _, code in matches
        )

    def resolve(
        self,
        request: str,
    ) -> str | None:

        result = self.resolve_result(request)

        if not result.is_resolved:
            return None

        return result.code
