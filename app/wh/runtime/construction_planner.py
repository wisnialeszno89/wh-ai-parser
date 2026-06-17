from app.wh.runtime.construction_strategy_factory import (
    ConstructionStrategyFactory
)


class ConstructionPlanner:

    def __init__(

        self

    ):

        self.factory = (

            ConstructionStrategyFactory()

        )

    def plan(

        self,

        construction

    ):

        strategy = (

            self.factory.create(

                construction.category

            )

        )

        return (

            strategy.plan(

                construction

            )

        )