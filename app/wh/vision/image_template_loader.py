import cv2

from app.wh.vision.image_template import (
    ImageTemplate
)


class ImageTemplateLoader:

    def load(

        self,

        path

    ):

        image = cv2.imread(

            path

        )

        return ImageTemplate(

            name=path,

            image=image

        )