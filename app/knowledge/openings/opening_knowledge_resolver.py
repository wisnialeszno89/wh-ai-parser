from app.knowledge.openings.opening_repository import (
    OpeningRepository,
)


class OpeningKnowledgeResolver:
    """
    Resolve a technical opening description into a
    canonical opening code using Knowledge.

    The resolver does not guess ambiguous or unknown
    descriptions.
    """

    def __init__(
        self,
        repository: OpeningRepository | None = None,
    ):
        self.repository = (
            repository
            or OpeningRepository()
        )

    def resolve(
        self,
        value: str,
    ) -> str | None:
        """
        Return the canonical opening code or None
        when the value is unknown or ambiguous.
        """

        definition = (
            self.repository.get_by_code_or_alias(
                value
            )
        )

        if definition is None:
            return None

        return definition.code
