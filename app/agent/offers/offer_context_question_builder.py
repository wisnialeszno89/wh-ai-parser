from app.agent.offers.offer_context_question_result import (
    OfferContextQuestionResult,
)

from app.agent.offers.offer_context_validation_result import (
    OfferContextValidationResult,
)


class OfferContextQuestionBuilder:
    """
    Build customer questions from offer context
    validation results.
    """

    FIELD_QUESTIONS = {
        "product_type": (
            "Jakiego rodzaju produktu potrzebujesz?"
        ),
        "width": (
            "Podaj proszę szerokość."
        ),
        "height": (
            "Podaj proszę wysokość."
        ),
    }

    CONFLICT_MESSAGES = {
        "invalid_quantity": (
            "Podana ilość musi być większa od zera."
        ),
        "invalid_width": (
            "Podana szerokość musi być większa od zera."
        ),
        "invalid_height": (
            "Podana wysokość musi być większa od zera."
        ),
    }

    def build(
        self,
        validation: OfferContextValidationResult,
    ) -> OfferContextQuestionResult:
        """
        Build questions and validation messages.
        """

        questions = tuple(
            self.FIELD_QUESTIONS[field]
            for field in validation.missing_fields
            if field in self.FIELD_QUESTIONS
        )

        messages = tuple(
            self.CONFLICT_MESSAGES[conflict]
            for conflict in validation.conflicts
            if conflict in self.CONFLICT_MESSAGES
        )

        return OfferContextQuestionResult(
            questions=questions,
            messages=messages,
        )
