import cv2

from app.wh.vision.match_result import (
    MatchResult,
)


class MultiScaleMatcher:

    def match(
        self,
        screenshot,
        template,
    ):

        if (
            len(screenshot.shape) == 3
            and screenshot.shape[2] == 4
        ):
            screenshot = cv2.cvtColor(
                screenshot,
                cv2.COLOR_BGRA2BGR,
            )

        if (
            len(template.shape) == 3
            and template.shape[2] == 4
        ):
            template = cv2.cvtColor(
                template,
                cv2.COLOR_BGRA2BGR,
            )

        best = None

        for scale in [
            0.7,
            0.8,
            0.9,
            1.0,
            1.1,
            1.2,
            1.3,
        ]:

            resized = cv2.resize(
                template,
                None,
                fx=scale,
                fy=scale,
            )

            result = cv2.matchTemplate(
                screenshot,
                resized,
                cv2.TM_CCOEFF_NORMED,
            )

            _, confidence, _, location = cv2.minMaxLoc(
                result
            )

            x, y = location

            height, width = resized.shape[:2]

            current = MatchResult(
                found=True,
                x=x,
                y=y,
                width=width,
                height=height,
                confidence=float(confidence),
            )

            if (
                best is None
                or current.confidence > best.confidence
            ):
                best = current

        return best