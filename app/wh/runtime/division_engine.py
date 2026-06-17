from app.wh.runtime.canvas_locator import (
    CanvasLocator
)

from app.wh.runtime.division_point_calculator import (
    DivisionPointCalculator
)

from app.wh.runtime.division_action_generator import (
    DivisionActionGenerator
)

from app.wh.runtime.division_executor import (
    DivisionExecutor
)


class DivisionEngine:

    def __init__(

        self

    ):

        self.locator = CanvasLocator()

        self.calculator = DivisionPointCalculator()

        self.generator = DivisionActionGenerator()

        self.executor = DivisionExecutor()

    def build_division(

        self,

        construction

    ):

        if not construction.division:

            return []

        canvas = self.locator.locate()

        points = self.calculator.calculate_x_points(

            construction,

            canvas

        )

        actions = self.generator.generate(

            points

        )

        return self.executor.execute(

            actions

        )