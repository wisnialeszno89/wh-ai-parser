from app.wh.runtime.fields.field import (
    Field
)


class FieldFactory:

    def create(

        self,

        data

    ):

        return Field(

            id=data["id"],

            x=data["x"],

            y=data["y"],

            opening=data.get(

                "opening",

                ""

            ),

            actions=data.get(

                "actions"

            )

        )