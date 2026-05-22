class SegmentGeometry:

    @staticmethod
    def calculate_positions(

        bounds,
        layout
    ):

        width = (
            bounds[2] -
            bounds[0]
        )

        current_x = bounds[0]

        positions = []

        for segment in layout:

            segment_width = int(
                width *
                segment.width_ratio
            )

            center_x = (
                current_x +
                segment_width // 2
            )

            positions.append(
                center_x
            )

            current_x += (
                segment_width
            )

        return positions