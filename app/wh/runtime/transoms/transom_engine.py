from app.wh.runtime.transoms.transom import (
    Transom
)


class TransomEngine:

    def calculate(

        self,

        top_fields,

        bottom_fields=None

    ):

        if bottom_fields is None:

            return []

        transoms = []

        count = min(

            len(

                top_fields

            ),

            len(

                bottom_fields

            )

        )

        for i in range(

            count

        ):

            transoms.append(

                Transom(

                    top_field=top_fields[i],

                    bottom_field=bottom_fields[i]

                )

            )

        return transoms