from app.wh.vision.opencv.opencv_adapter import (
    OpenCVAdapter
)

from app.wh.vision.image_repository import (
    ImageRepository
)

from app.wh.vision.image_loader import (
    ImageLoader
)


class TemplateMatcher:

    def __init__(

        self

    ):

        self.cv = OpenCVAdapter()

        self.repository = ImageRepository()

        self.loader = ImageLoader()

    def locate(

        self,

        screenshot,

        name

    ):

        template = self.repository.get(

            name

        )

        image = self.loader.load(

            template.file_name

        )

        return self.cv.match_template(

            screenshot,

            image

        )