class FieldNeighbourEngine:

    def left(

        self,

        field,

        mullions

    ):

        for mullion in mullions:

            if mullion.right_field == field:

                return mullion.left_field

        return None

    def right(

        self,

        field,

        mullions

    ):

        for mullion in mullions:

            if mullion.left_field == field:

                return mullion.right_field

        return None

    def top(

        self,

        field,

        transoms

    ):

        for transom in transoms:

            if transom.bottom_field == field:

                return transom.top_field

        return None

    def bottom(

        self,

        field,

        transoms

    ):

        for transom in transoms:

            if transom.top_field == field:

                return transom.bottom_field

        return None