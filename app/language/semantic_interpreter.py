from app.context.offer_context import OfferContext


class SemanticInterpreter:

    def interpret(
        self,
        text: str
    ) -> OfferContext:

        context = OfferContext()

        text = text.lower()

        if "veka" in text:
            context.profile = "VEKA"

        if "82" in text:
            context.profile_variant = "82"

        if "perfect" in text:
            context.glass_package = "PERFECT"

        if "3 szyby" in text:
            context.glazing = 3

        if "2 szyby" in text:
            context.glazing = 2

        if "rup" in text:
            context.construction_type = "RUP"

        return context