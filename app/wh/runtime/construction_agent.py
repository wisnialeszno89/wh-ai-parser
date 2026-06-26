from app.wh.runtime.construction_parser import (
    ConstructionParser
)

from app.wh.runtime.construction_executor import (
    ConstructionExecutor
)


class ConstructionAgent:

    def __init__(

        self

    ):

        self.parser = (

            ConstructionParser()

        )

        self.executor = (

            ConstructionExecutor()

        )

    def execute(

        self,

        text

    ):

        construction = (

            self.parser.parse(

                text

            )

        )

        return (

            self.executor.execute(

                construction

            )

        )