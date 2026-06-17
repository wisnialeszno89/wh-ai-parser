from app.wh.runtime.division_point_calculator import (
    DivisionPointCalculator
)

from app.wh.runtime.construction_schema import (
    ConstructionSchema
)

from app.wh.runtime.canvas_geometry import (
    CanvasGeometry
)


def test_division_point_calculator():

    calculator = DivisionPointCalculator()

    construction = ConstructionSchema(

        width=1500,

        height=1400,

        schema="basic_window",

        division=True,

        ratio_x=[30,70]

    )

    canvas = CanvasGeometry(

        left=100,

        top=200,

        right=1600,

        bottom=1200

    )

    points = calculator.calculate_x_points(

        construction,

        canvas

    )

    assert points == [

        550,

        1150

    ]