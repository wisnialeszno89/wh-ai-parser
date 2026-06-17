from app.wh.runtime.hst_construction_strategy import (
    HSTConstructionStrategy
)

from app.wh.runtime.window_construction_strategy import (
    WindowConstructionStrategy
)


class ConstructionStrategyFactory:

    def create(

        self,

        category

    ):

        if category == "window":

            return (

                WindowConstructionStrategy()

            )

        if category == "hst":

            return (

                HSTConstructionStrategy()

            )

        raise RuntimeError(

            f"Unsupported category: "

            f"{category}"

        )