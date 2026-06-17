class ColumnClusterEngine:

    def cluster(

        self,

        fields

    ):

        columns = {}

        for field in fields:

            x = field.x

            if x not in columns:

                columns[x] = []

            columns[x].append(

                field

            )

        return list(

            columns.values()

        )