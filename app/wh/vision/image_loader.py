from app.wh.vision.image import (
    Image
)

from app.wh.vision.image_size import (
    ImageSize
)


class ImageLoader:

    def load(

        self,

        file_name

    ):

        return Image(

            file_name=file_name,

            size=ImageSize(

                width=300,

                height=50

            )

        )