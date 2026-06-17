from app.wh.vision.opencv.opencv_adapter import (
    OpenCVAdapter
)


class MultipleTemplatesMatcher:

    def __init__(

        self

    ):

        self.matcher = (

            OpenCVAdapter()

        )

    def match(

        self,

        screenshot,

        templates

    ):

        best_template = None

        best_result = None

        for template in templates:

            result = (

                self.matcher.match_array(

                    screenshot.image,

                    template.image

                )

            )

            if (

                best_result is None

                or

                result.confidence

                >

                best_result.confidence

            ):

                best_template = template

                best_result = result

        return (

            best_template,

            best_result

        )