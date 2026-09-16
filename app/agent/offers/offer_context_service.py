from app.agent.offers.offer_context_parser import (
    OfferContextParser,
)

from app.agent.offers.offer_context_service_result import (
    OfferContextServiceResult,
)

from app.agent.offers.offer_context_validator import (
    OfferContextValidator,
)


class OfferContextService:
    """
    Process a raw quotation request into a normalized
    and validated offer context.

    The service coordinates parsing and validation
    without owning the extraction or business rules.
    """

    def __init__(
        self,
        parser: OfferContextParser | None = None,
        validator: OfferContextValidator | None = None,
    ) -> None:

        self.parser = (
            parser
            if parser is not None
            else OfferContextParser()
        )

        self.validator = (
            validator
            if validator is not None
            else OfferContextValidator()
        )

    def process(
        self,
        raw_request: str,
    ) -> OfferContextServiceResult:
        """
        Parse and validate a quotation request.
        """

        context = self.parser.parse(
            raw_request
        )

        validation = self.validator.validate(
            context
        )

        return OfferContextServiceResult(
            context=context,
            validation=validation,
        )
