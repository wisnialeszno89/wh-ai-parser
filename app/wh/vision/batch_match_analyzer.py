import cv2
from pathlib import Path

from app.wh.vision.hybrid_matcher import (
    HybridMatcher
)


class BatchMatchAnalyzer:

    def analyze(

        self,

        screens_dir,

        template_path

    ):

        matcher = HybridMatcher()

        reports = []

        for screen_path in sorted(

            Path(

                screens_dir

            ).glob(

                "*.png"

            )

        ):

            screenshot = cv2.imread(

                str(

                    screen_path

                )

            )

            template = cv2.imread(

                template_path

            )

            result = matcher.match(

                screenshot,

                template

            )

            reports.append(

                (

                    screen_path.name,

                    matcher.last_report

                )

            )

        return reports