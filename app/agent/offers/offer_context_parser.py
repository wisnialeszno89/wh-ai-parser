import re

from app.agent.offers.offer_context import (
    OfferContext,
)
from app.agent.offers.profile_selection import (
    ProfileSelectionResolver,
)
from app.knowledge.openings.offer_opening_resolver import (
    OfferOpeningResolver,
)
from app.knowledge.constructions.construction_resolver import (
    ConstructionResolver,
)


class OfferContextParser:
    """
    Parse a salesman quotation request into a normalized
    OfferContext.

    The first implementation intentionally uses simple,
    deterministic rules. More advanced NLP or LLM-based
    extraction can be added later without changing the
    OfferContext contract.
    """

    def __init__(
        self,
        opening_resolver: OfferOpeningResolver | None = None,
        profile_selection_resolver: ProfileSelectionResolver | None = None,
        construction_resolver: ConstructionResolver | None = None,
    ):
        self.opening_resolver = (
            opening_resolver or OfferOpeningResolver()
        )
        self.profile_selection_resolver = (
            profile_selection_resolver or ProfileSelectionResolver()
        )
        self.construction_resolver = (
            construction_resolver or ConstructionResolver()
        )

    def parse(
        self,
        request: str,
    ) -> OfferContext:
        """
        Parse a raw quotation request.
        """

        normalized_request = (
            request
            .strip()
            .lower()
        )

        quantity = self._parse_quantity(
            normalized_request
        )

        width, height = (
            self._parse_dimensions(
                normalized_request
            )
        )

        product_type = (
            self._parse_product_type(
                normalized_request
            )
        )

        profile_selection = self.profile_selection_resolver.resolve(
            request
        )

        configuration = (
            self._parse_configuration(
                normalized_request
            )
        )

        openings = (
            self.opening_resolver.resolve_all(
                request
            )
        )

        opening_resolution = (
            self.opening_resolver.resolve_result(
                request
            )
        )

        known_construction = (
            self.construction_resolver.resolve(
                list(openings)
            )
            if len(openings) > 1
            else None
        )

        opening = (
            opening_resolution.code
            if opening_resolution.is_resolved
            else None
        )

        color_inside = (
            self._parse_inside_color(
                normalized_request
            )
        )

        color_outside = (
            self._parse_outside_color(
                normalized_request
            )
        )

        glazing = (
            self._parse_glazing(
                normalized_request
            )
        )

        missing_fields = (
            self._determine_missing_fields(
                width=width,
                height=height,
                product_type=product_type,
            )
        )

        conflicts = list(
            self._determine_conflicts(
                width=width,
                height=height,
            )
        )

        if profile_selection.source.value == "UNKNOWN":
            conflicts.append(profile_selection.reason)

        if opening_resolution.is_ambiguous:
            if opening_resolution.matches:
                if known_construction is None:
                    conflicts.append(
                        "Ambiguous opening: "
                        + ", ".join(
                            opening_resolution.matches
                        )
                    )
            else:
                conflicts.append(
                    "Ambiguous opening: "
                    "opening direction is missing."
                )

        unspecified_ral_color = (
            self._parse_unspecified_ral_color(
                normalized_request
            )
        )

        if (
            unspecified_ral_color is not None
            and color_inside is None
            and color_outside is None
            and "od środka" not in normalized_request
            and "wewnątrz" not in normalized_request
            and "z zewnątrz" not in normalized_request
            and "na zewnątrz" not in normalized_request
            and "obustronnie" not in normalized_request
        ):
            conflicts.append(
                "Color code "
                + unspecified_ral_color
                + " was provided without "
                "specifying the side."
            )

        conflicts = tuple(conflicts)

        return OfferContext(
            raw_request=request,
            width=width,
            height=height,
            quantity=quantity,
            product_type=product_type,
            profile=profile_selection.profile,
            profile_source=profile_selection.source,
            configuration=configuration,
            opening=opening,
            openings=openings,
            color_inside=color_inside,
            color_outside=color_outside,
            glazing=glazing,
            missing_fields=missing_fields,
            conflicts=conflicts,
        )

    def _parse_quantity(
        self,
        request: str,
    ) -> int:

        patterns = (
            r"\b(\d+)\s*(?:x|szt\.?|sztuk|sztuki)\b",
            r"\bpotrzebuję\s+(\d+)\b",
            r"\bchcę\s+(\d+)\b",
        )

        for pattern in patterns:

            match = re.search(
                pattern,
                request,
            )

            if match:

                return int(
                    match.group(1)
                )

        return 1

    def _parse_dimensions(
        self,
        request: str,
    ) -> tuple[int | None, int | None]:

        pattern = (
            r"\b(\d{2,4})\s*[x×]\s*(\d{2,4})\b"
        )

        match = re.search(
            pattern,
            request,
        )

        if not match:

            return (
                None,
                None,
            )

        width = int(
            match.group(1)
        )

        height = int(
            match.group(2)
        )

        return (
            width,
            height,
        )

    def _parse_product_type(
        self,
        request: str,
    ) -> str | None:

        product_types = {
            "okno": "window",
            "okna": "window",
            "okien": "window",
            "window": "window",

            "drzwi": "door",
            "drzwiowe": "door",
            "door": "door",

            "drzwi balkonowe": (
                "balcony_door"
            ),

            "hs": "sliding_door",
            "h.s.": "sliding_door",
            "przesuwne": "sliding_door",
        }

        for phrase, value in (
            product_types.items()
        ):

            if phrase in request:

                return value

        return None

    def _parse_configuration(
        self,
        request: str,
    ) -> str | None:

        configurations = {
            "jednoskrzydłowe": (
                "single_leaf"
            ),
            "jednoskrzydłowe": (
                "single_leaf"
            ),
            "dwuskrzydłowe": (
                "double_leaf"
            ),
            "dwuskrzydłowe": (
                "double_leaf"
            ),
            "fix": "fixed",
            "nieotwierane": "fixed",
        }

        for phrase, value in (
            configurations.items()
        ):

            if phrase in request:

                return value

        return None

    def _parse_inside_color(
        self,
        request: str,
    ) -> str | None:

        color_patterns = {
            "biały": "white",
            "białe": "white",
            "biała": "white",
            "antracyt": "anthracite",
            "czarny": "black",
            "brąz": "brown",
        }

        pattern = (
            r"(biały|białe|biała|antracyt|"
            r"czarny|brąz)"
            r"\s+(?:od środka|wewnątrz)"
        )

        match = re.search(
            pattern,
            request,
        )

        if match:
            return color_patterns.get(
                match.group(1)
            )

        ral_match = re.search(
            r"\b(?:kolor\s+)?(\d{4})\s+"
            r"(?:od środka|wewnątrz|obustronnie)\b",
            request,
        )

        if ral_match:
            return ral_match.group(1)

        return None

    def _parse_outside_color(
        self,
        request: str,
    ) -> str | None:

        color_patterns = {
            "biały": "white",
            "białe": "white",
            "biała": "white",
            "antracyt": "anthracite",
            "czarny": "black",
            "brąz": "brown",
        }

        pattern = (
            r"(biały|białe|biała|antracyt|"
            r"czarny|brąz)"
            r"\s+(?:z zewnątrz|na zewnątrz)"
        )

        match = re.search(
            pattern,
            request,
        )

        if match:
            return color_patterns.get(
                match.group(1)
            )

        ral_match = re.search(
            r"\b(?:kolor\s+)?(\d{4})\s+"
            r"(?:z zewnątrz|na zewnątrz|obustronnie)\b",
            request,
        )

        if ral_match:
            return ral_match.group(1)

        return None

    def _parse_unspecified_ral_color(
        self,
        request: str,
    ) -> str | None:

        match = re.search(
            r"\b(?:kolor\s+)?(\d{4})\b",
            request,
        )

        if not match:
            return None

        return match.group(1)

    def _parse_glazing(
        self,
        request: str,
    ) -> str | None:

        glazing_types = {
            "dwuszybowe": "double",
            "dwuszybowe": "double",
            "2 szyb": "double",
            "dwuszybowe": "double",

            "trzyszybowe": "triple",
            "3 szyb": "triple",
            "trzyszybowe": "triple",
        }

        for phrase, value in (
            glazing_types.items()
        ):

            if phrase in request:

                return value

        return None

    def _determine_missing_fields(
        self,
        *,
        width: int | None,
        height: int | None,
        product_type: str | None,
    ) -> tuple[str, ...]:

        missing_fields = []

        if product_type is None:

            missing_fields.append(
                "product_type"
            )

        if width is None:

            missing_fields.append(
                "width"
            )

        if height is None:

            missing_fields.append(
                "height"
            )

        return tuple(
            missing_fields
        )

    def _determine_conflicts(
        self,
        *,
        width: int | None,
        height: int | None,
    ) -> tuple[str, ...]:

        conflicts = []

        if (
            width is not None
            and width <= 0
        ):

            conflicts.append(
                "invalid_width"
            )

        if (
            height is not None
            and height <= 0
        ):

            conflicts.append(
                "invalid_height"
            )

        return tuple(
            conflicts
        )
