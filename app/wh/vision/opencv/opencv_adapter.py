import cv2

from app.wh.vision.match_result import (
    MatchResult,
)


class OpenCVAdapter:

    def match(
        self,
        screenshot_path,
        template_path,
    ):

        screenshot = cv2.imread(
            screenshot_path
        )

        if screenshot is None:
            raise RuntimeError(
                f"Cannot load screenshot: {screenshot_path}"
            )

        template = cv2.imread(
            template_path
        )

        if template is None:
            raise RuntimeError(
                f"Cannot load template: {template_path}"
            )

        return self.match_array(
            screenshot,
            template,
        )

    def match_array(
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

        result = cv2.matchTemplate(
            screenshot,
            template,
            cv2.TM_CCOEFF_NORMED,
        )

        _, confidence, _, location = cv2.minMaxLoc(
            result
        )

        x, y = location

        height, width = template.shape[:2]

        return MatchResult(
            found=True,
            x=x,
            y=y,
            width=width,
            height=height,
            confidence=float(confidence),
        )