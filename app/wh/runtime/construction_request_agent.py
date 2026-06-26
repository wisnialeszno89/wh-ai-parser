from app.wh.runtime.construction_request_parser import (
    ConstructionRequestParser
)

from app.wh.runtime.construction_normalizer import (
    ConstructionNormalizer
)

from app.wh.runtime.construction_parser import (
    ConstructionParser
)

from app.wh.runtime.offer_enricher import (
    OfferEnricher
)

from app.wh.runtime.construction_project import (
    ConstructionProject
)


class ConstructionRequestAgent:

    def __init__(

        self

    ):

        self.request_parser = (

            ConstructionRequestParser()

        )

        self.normalizer = (

            ConstructionNormalizer()

        )

        self.parser = (

            ConstructionParser()

        )

        self.offer_enricher = (

            OfferEnricher()

        )

    def parse(

        self,

        text

    ):

        request = (

            self.request_parser.parse(

                text

            )

        )

        notation = (

            self.normalizer.normalize(

                request.notation

            )

        )

        construction = (

            self.parser.parse(

                notation

            )

        )

        construction.width = (

            request.width

        )

        construction.height = (

            request.height

        )

        offer = (

            self.offer_enricher.enrich(

                text

            )

        )

        return (

            ConstructionProject(

                schema=construction,

                offer=offer

            )

        )