from app.agent.offers.offer_context import (
    OfferContext,
)

from app.agent.offers.profile_selection import (
    ProfileSelectionSource,
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

        profile = existing.profile
        profile_source = existing.profile_source
        # Validation is recomputed after the merge; never carry stale conflicts.
        conflicts = []

        if (
            update.profile_source
            == ProfileSelectionSource.EXPLICIT
            and update.profile is not None
        ):
            profile = update.profile
            profile_source = update.profile_source

        elif (
            update.profile_source
            == ProfileSelectionSource.UNKNOWN
        ):
            profile = None
            profile_source = ProfileSelectionSource.UNKNOWN

        elif (
            existing.profile is None
            and update.profile_source
            == ProfileSelectionSource.DEFAULT
            and update.profile is not None
        ):
            profile = update.profile
            profile_source = update.profile_source

        if profile_source == ProfileSelectionSource.UNKNOWN:
            conflicts.append(
                "Profile was mentioned but could not be resolved."
            )

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
            profile=profile,
            profile_source=profile_source,
            configuration=(
                update.configuration
                if update.configuration is not None
                else existing.configuration
            ),
            opening=(
                update.opening
                if update.openings or update.opening is not None
                else existing.opening
            ),
            openings=(
                update.openings
                if update.openings
                else (
                    (update.opening,)
                    if update.opening is not None
                    else existing.openings
                )
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
            missing_fields=(),
            conflicts=tuple(conflicts),
        )
