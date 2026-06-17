class SegmentOpeningResolver:

    def resolve(

        self,

        segments

    ):

        openings = []

        for segment in segments:

            openings.append(

                segment.opening

            )

        return openings