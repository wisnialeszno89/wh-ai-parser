from app.wh.runtime.horizontal_division_point_calculator import (
    HorizontalDivisionPointCalculator
)

from app.wh.runtime.construction_schema import (
    ConstructionSchema
)

from app.wh.runtime.canvas_geometry import (
    CanvasGeometry
)


def test_horizontal_division_point_calculator():

    calculator = HorizontalDivisionPointCalculator()

    construction = ConstructionSchema(

        width=1500,

        height=1400,

        schema="basic_window",

        division=True,

        ratio_y=[50]

    )

    canvas = CanvasGeometry(

        left=100,

        top=200,

        right=1600,

        bottom=1200

    )

    points = calculator.calculate_y_points(

        construction,

        canvas

    )

    assert points == [

        700

    ]