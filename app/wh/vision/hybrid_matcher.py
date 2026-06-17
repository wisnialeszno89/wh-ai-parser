from app.wh.vision.opencv.opencv_adapter import (
    OpenCVAdapter
)

from app.wh.vision.grayscale_matcher import (
    GrayScaleMatcher
)

from app.wh.vision.multi_scale_matcher import (
    MultiScaleMatcher
)

from app.wh.vision.match_report import (
    MatchReport
)

class HybridMatcher:

    def __init__(

        self

    ):

        self.normal = (

            OpenCVAdapter()

        )

        self.gray = (

            GrayScaleMatcher()

        )

        self.multiscale = (

            MultiScaleMatcher()

        )

    def match(

        self,

        screenshot,

        template

    ):

        normal = (

            self.normal.match_array(

                screenshot,

                template

            )

        )

        gray = (

            self.gray.match(

                screenshot,

                template

            )

        )

        multiscale = (

            self.multiscale.match(

                screenshot,

                template

            )

        )

        candidates = [

            (

                "normal",

                normal

            ),

            (

                "gray",

                gray

            ),

            (

                "multiscale",

                multiscale

            )

        ]

        winner = max(

            candidates,

            key=lambda x:

            x[1].confidence

        )

        print()

        print(

            f"NORMAL      {normal.confidence:.3f}"

        )

        print(

            f"GRAY        {gray.confidence:.3f}"

        )

        print(

            f"MULTISCALE  {multiscale.confidence:.3f}"

        )

        print()

        print(

            f"WINNER = {winner[0]}"

        )
        self.last_report = MatchReport(

        normal=normal.confidence,

        gray=gray.confidence,

        multiscale=multiscale.confidence,

        winner=winner[0]

    )
        return winner[1]