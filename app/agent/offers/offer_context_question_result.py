from dataclasses import dataclass


@dataclass(frozen=True)
class OfferContextQuestionResult:
    """
    Questions generated from offer context validation.

    The result keeps missing information and detected
    conflicts separate so the conversation layer can
    decide how to present them to the customer.
    """

    questions: tuple[str, ...] = ()

    messages: tuple[str, ...] = ()

    @property
    def requires_response(self) -> bool:
        """
        Return whether customer input is required.
        """

        return bool(
            self.questions
        )
