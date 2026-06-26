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

        cols = (

            len(

                schema.ratio_x

            )

            + 1

        )

        rows = (

            len(

                schema.ratio_y

            )

            + 1

        )

        field_rows = []

        for row in range(

            rows

        ):

            start = (

                row

                * cols

            )

            end = (

                start

                + cols

            )

            field_rows.append(

                fields[

                    start:end

                ]

            )

        mullions = []

        for field_row in field_rows:

            mullions.extend(

                self.mullion_engine.calculate(

                    field_row

                )

            )

        transoms = []

        if rows > 1:

            for row in range(

                rows - 1

            ):

                transoms.extend(

                    self.transom_engine.calculate(

                        field_rows[row],

                        field_rows[row + 1]

                    )

                )

        return Construction(

            fields=fields,

            mullions=mullions,

            transoms=transoms

        )