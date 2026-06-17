from pathlib import Path

import cv2

from app.wh.vision.hybrid_matcher import (
    HybridMatcher
)


class TemplateCompetition:

    def run(

        self,

        screenshot_path,

        templates_dir

    ):

        screenshot = cv2.imread(

            screenshot_path

        )

        matcher = HybridMatcher()

        best_name = None

        best_result = None

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

                screenshot,

                template

            )

            if (

                best_result is None

                or

                result.confidence

                >

                best_result.confidence

            ):

                best_result = result

                best_name = (

                    template_path.name

                )

        print()

        print(

            "WINNER TEMPLATE:"

        )

        print(

            best_name

        )

        print(

            f"CONFIDENCE={best_result.confidence:.3f}"

        )

        return (

            best_name,

            best_result

        )