class FindObject:

    def find(

        self,

        objects,

        name

    ):

        for obj in objects:

            if (

                obj.name

                ==

                name

            ):

                return obj

        raise RuntimeError(

            f"Object not found: "

            f"{name}"

        )