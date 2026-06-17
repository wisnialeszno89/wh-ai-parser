from app.wh.runtime.patterns.single_row_recognizer import (
    SingleRowRecognizer
)

from app.wh.runtime.patterns.single_column_recognizer import (
    SingleColumnRecognizer
)

from app.wh.runtime.patterns.balanced_grid_recognizer import (
    BalancedGridRecognizer
)


class TopologyClassifier:

    def __init__(

        self

    ):

        self.single_row = (

            SingleRowRecognizer()

        )

        self.single_column = (

            SingleColumnRecognizer()

        )

        self.balanced_grid = (

            BalancedGridRecognizer()

        )

    def classify(

        self,

        signature

    ):

        labels = []

        if self.single_row.matches(

            signature

        ):

            labels.append(

                "single_row"

            )

        if self.single_column.matches(

            signature

        ):

            labels.append(

                "single_column"

            )

        if self.balanced_grid.matches(

            signature

        ):

            labels.append(

                "balanced_grid"

            )

        return labels