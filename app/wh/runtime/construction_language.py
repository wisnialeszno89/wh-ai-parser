class ConstructionLanguage:

    def describe(

        self,

        construction

    ):

        names = []

        for segment in (

            construction.segments

        ):

            names.append(

                segment.opening.value

            )

        return "+".join(

            names

        )