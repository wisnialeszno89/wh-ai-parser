class RowClusterEngine:

    def cluster(

        self,

        fields

    ):

        rows = {}

        for field in fields:

            y = field.y

            if y not in rows:

                rows[y] = []

            rows[y].append(

                field

            )

        return list(

            rows.values()

        )