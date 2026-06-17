class CanvasGeometry:

    def __init__(

        self,

        left,

        top,

        right,

        bottom

    ):

        self.left = left

        self.top = top

        self.right = right

        self.bottom = bottom

    @property
    def center_x(

        self

    ):

        return (

            self.left +

            self.right

        ) // 2

    @property
    def center_y(

        self

    ):

        return (

            self.top +

            self.bottom

        ) // 2