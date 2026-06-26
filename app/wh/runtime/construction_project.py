from dataclasses import (
    dataclass
)

from app.wh.runtime.construction_schema import (
    ConstructionSchema
)

from app.wh.runtime.construction_offer import (
    ConstructionOffer
)


@dataclass
class ConstructionProject:

    schema: ConstructionSchema

    offer: ConstructionOffer