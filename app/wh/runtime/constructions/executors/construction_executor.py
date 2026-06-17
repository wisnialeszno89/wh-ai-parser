from app.wh.runtime.field_executor import (
    FieldExecutor
)

from app.wh.runtime.mullions.mullion_executor import (
    MullionExecutor
)

from app.wh.runtime.transoms.transom_executor import (
    TransomExecutor
)


class ConstructionExecutor:

    def __init__(

        self

    ):

        self.field_executor = (

            FieldExecutor()

        )

        self.mullion_executor = (

            MullionExecutor()

        )

        self.transom_executor = (

            TransomExecutor()

        )

    def execute(

        self,

        construction

    ):

        self.field_executor.execute(

            construction.fields

        )

        self.mullion_executor.execute(

            construction.mullions

        )

        self.transom_executor.execute(

            construction.transoms

        )

        return True