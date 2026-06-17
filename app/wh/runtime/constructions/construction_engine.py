from app.wh.runtime.grid.grid_field_engine import (
    GridFieldEngine
)

from app.wh.runtime.field_classifier import (
    FieldClassifier
)

from app.wh.runtime.field_action_planner import (
    FieldActionPlanner
)

from app.wh.runtime.mullions.mullion_engine import (
    MullionEngine
)

from app.wh.runtime.transoms.transom_engine import (
    TransomEngine
)

from app.wh.runtime.constructions.construction import (
    Construction
)


class ConstructionEngine:

    def __init__(

        self

    ):

        self.grid_engine = (

            GridFieldEngine()

        )

        self.classifier = (

            FieldClassifier()

        )

        self.planner = (

            FieldActionPlanner()

        )

        self.mullion_engine = (

            MullionEngine()

        )

        self.transom_engine = (

            TransomEngine()

        )

    def build(

        self,

        schema

    ):

        fields = (

            self.grid_engine.build(

                schema.ratio_x,

                schema.ratio_y

            )

        )

        fields = (

            self.classifier.classify(

                fields,

                schema

            )

        )

        fields = (

            self.planner.plan(

                fields

            )

        )

        mullions = (

            self.mullion_engine.calculate(

                fields

            )

        )

        transoms = (

            self.transom_engine.calculate(

                fields

            )

        )

        return Construction(

            fields=fields,

            mullions=mullions,

            transoms=transoms

        )