from app.wh.vision.field_region import (
    FieldRegion
)


class FieldRegionBuilder:

    def build(

        self,

        fields

    ):

        regions = []

        for field in fields:

            regions.append(

                FieldRegion(

                    left=field.x - 100,

                    top=field.y - 100,

                    right=field.x + 100,

                    bottom=field.y + 100,

                    id=field.id,

                    opening=field.opening

                )

            )

        return regions