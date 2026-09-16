from app.agent.offers.offer_context import (
    OfferContext,
)


class OfferContextMerger:
    """
    Merge a newly extracted OfferContext into an
    existing quotation context.

    Existing values are preserved when the update
    does not provide a meaningful replacement.

    Explicit values from the update take precedence.
    """

    def merge(
        self,
        existing: OfferContext,
        update: OfferContext,
    ) -> OfferContext:
        """
        Merge an update context into an existing
        quotation context.
        """

        return OfferContext(
            raw_request=existing.raw_request,
            width=(
                update.width
                if update.width is not None
                else existing.width
            ),
            height=(
                update.height
                if update.height is not None
                else existing.height
            ),
            quantity=(
                update.quantity
                if update.quantity != 1
                else existing.quantity
            ),
            product_type=(
                update.product_type
                if update.product_type is not None
                else existing.product_type
            ),
            configuration=(
                update.configuration
                if update.configuration is not None
                else existing.configuration
            ),
            opening=(
                update.opening
                if update.opening is not None
                else existing.opening
            ),
            color_inside=(
                update.color_inside
                if update.color_inside is not None
                else existing.color_inside
            ),
            color_outside=(
                update.color_outside
                if update.color_outside is not None
                else existing.color_outside
            ),
            glazing=(
                update.glazing
                if update.glazing is not None
                else existing.glazing
            ),
        )
