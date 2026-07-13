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

        if screenshot is None:
            raise RuntimeError("Screenshot is None")

        if template is None:
            raise RuntimeError("Template is None")

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

        sh, sw = screenshot.shape[:2]
        th, tw = template.shape[:2]

        print()
        print("=" * 60)
        print("[MATCH]")
        print(f"SCREENSHOT : {sw}x{sh}")
        print(f"TEMPLATE   : {tw}x{th}")
        print("=" * 60)

        if th > sh or tw > sw:
            raise RuntimeError(
                f"Template {tw}x{th} larger than screenshot {sw}x{sh}"
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