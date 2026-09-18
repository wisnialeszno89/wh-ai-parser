class FieldClassifier:

    def classify(

        self,

        fields,

        schema

    ):

        for index, field in enumerate(

            fields

        ):

            if index < len(

                schema.segments

            ):

                field.opening = (

                    schema.segments[

                        index

                    ].opening

                )

                field.direction = (
                    schema.segments[
                        index
                    ].direction
                )
        return fields
