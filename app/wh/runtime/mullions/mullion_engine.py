from app.wh.runtime.mullions.mullion import (
    Mullion
)


class MullionEngine:

    def calculate(

        self,

        fields

    ):

        mullions = []

        if len(

            fields

        ) < 2:

            return mullions

        for i in range(

            len(fields)-1

        ):

            mullions.append(

                Mullion(

                    left_field=fields[i],

                    right_field=fields[i+1]

                )

            )

        return mullions