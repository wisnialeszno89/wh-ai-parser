class GridTopologyEngine:

    def build(

        self,

        fields

    ):

        rows = {}

        for field in fields:

            if field.y not in rows:

                rows[field.y] = []

            rows[field.y].append(

                field

            )

        topology = []

        for y in sorted(

            rows.keys()

        ):

            row = sorted(

                rows[y],

                key=lambda f: f.x

            )

            topology.append(

                row

            )

        return topology