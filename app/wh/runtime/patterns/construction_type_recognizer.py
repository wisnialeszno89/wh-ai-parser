from app.wh.runtime.patterns.single_row_construction_recognizer import (
    SingleRowConstructionRecognizer
)

from app.wh.runtime.patterns.single_column_construction_recognizer import (
    SingleColumnConstructionRecognizer
)

from app.wh.runtime.patterns.balanced_grid_construction_recognizer import (
    BalancedGridConstructionRecognizer
)


class ConstructionTypeRecognizer:

    def __init__(

        self

    ):

        self.recognizers = [

            SingleRowConstructionRecognizer(),

            SingleColumnConstructionRecognizer(),

            BalancedGridConstructionRecognizer()

        ]

    def recognize(

        self,

        context

    ):

        result = []

        for recognizer in (

            self.recognizers

        ):

            if recognizer.matches(

                context

            ):

                result.append(

                    recognizer.name()

                )

        return result