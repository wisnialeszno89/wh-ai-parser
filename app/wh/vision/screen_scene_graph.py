from pathlib import Path

import cv2

from app.wh.vision.hybrid_matcher import (
    HybridMatcher
)

from app.wh.vision.screen_object import (
    ScreenObject
)

from app.wh.vision.screenshot import (
    Screenshot
)


class ScreenSceneGraph:

    def analyze(

        self,

        screenshot,

        templates_dir

    ):

        if isinstance(

            screenshot,

            Screenshot

        ):

            screenshot_image = (

                screenshot.image

            )

        else:

            screenshot_image = cv2.imread(

                screenshot

            )

        matcher = HybridMatcher()

        objects = []

        for template_path in sorted(

            Path(

                templates_dir

            ).glob(

                "*.png"

            )

        ):

            template = cv2.imread(

                str(

                    template_path

                )

            )

            result = matcher.match(

                screenshot_image,

                template

            )

            objects.append(

                ScreenObject(

                    name=template_path.name,

                    x=result.x,

                    y=result.y,

                    width=result.width,

                    height=result.height,

                    confidence=result.confidence

                )

            )

        objects.sort(

            key=lambda obj:

            obj.confidence,

            reverse=True

        )

        return objects