from dataclasses import dataclass


@dataclass(frozen=True)
class OfferContextValidationResult:
    """
    Result of validating an OfferContext.

    Validation determines whether the extracted
    business context contains enough consistent
    information to continue the quotation workflow.
    """

    is_valid: bool

    missing_fields: tuple[str, ...] = ()

    conflicts: tuple[str, ...] = ()
