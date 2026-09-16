from app.agent.offers.offer_context import (
    OfferContext,
)

from app.agent.offers.offer_context_validation_result import (
    OfferContextValidationResult,
)


class OfferContextValidator:
    """
    Validate normalized quotation context.

    The validator intentionally owns the business
    validation rules while OfferContextParser is only
    responsible for extracting information.
    """

    REQUIRED_FIELDS = (
        "product_type",
        "width",
        "height",
    )

    def validate(
        self,
        context: OfferContext,
    ) -> OfferContextValidationResult:
        """
        Validate an offer context.
        """

        missing_fields = list(
            context.missing_fields
        )

        conflicts = list(
            context.conflicts
        )

        values = {
            "product_type": (
                context.product_type
            ),
            "width": context.width,
            "height": context.height,
        }

        for field in self.REQUIRED_FIELDS:

            if (
                values[field] is None
                and field not in missing_fields
            ):

                missing_fields.append(
                    field
                )

        if (
            context.quantity <= 0
        ):

            conflicts.append(
                "invalid_quantity"
            )

        if (
            context.width is not None
            and context.width <= 0
        ):

            conflicts.append(
                "invalid_width"
            )

        if (
            context.height is not None
            and context.height <= 0
        ):

            conflicts.append(
                "invalid_height"
            )

        missing_fields = tuple(
            dict.fromkeys(
                missing_fields
            )
        )

        conflicts = tuple(
            dict.fromkeys(
                conflicts
            )
        )

        return OfferContextValidationResult(
            is_valid=(
                not missing_fields
                and not conflicts
            ),
            missing_fields=missing_fields,
            conflicts=conflicts,
        )
