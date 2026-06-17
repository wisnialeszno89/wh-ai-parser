from app.wh.vision.image_template import (
    ImageTemplate
)


class ImageRepository:

    def get(

        self,

        name

    ):

        return ImageTemplate(

            name=name,

            file_name=f"{name}_combobox.png"

        )