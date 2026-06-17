import cv2

from app.wh.vision.match_result import (
    MatchResult
)


class DebugMultiScaleMatcher:

    def match(

        self,

        screenshot,

        template

    ):

        best = None

        best_scale = None

        for scale in [

            0.6,
            0.7,
            0.8,
            0.9,
            1.0,
            1.1,
            1.2,
            1.3,
            1.4

        ]:

            resized = cv2.resize(

                template,

                None,

                fx=scale,

                fy=scale

            )

            result = cv2.matchTemplate(

                screenshot,

                resized,

                cv2.TM_CCOEFF_NORMED

            )

            _, confidence, _, location = (

                cv2.minMaxLoc(

                    result

                )

            )

            print(

                f"scale={scale} confidence={confidence:.3f}"

            )

            x, y = location

            height, width = resized.shape[:2]

            candidate = MatchResult(

                x=x,

                y=y,

                width=width,

                height=height,

                confidence=float(

                    confidence

                )

            )

            if (

                best is None

                or

                candidate.confidence > best.confidence

            ):

                best = candidate

                best_scale = scale

        print()

        print(

            f"BEST SCALE={best_scale}"

        )

        print(

            f"BEST CONFIDENCE={best.confidence:.3f}"

        )

        return best