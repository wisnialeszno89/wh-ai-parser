import cv2


class HeatMapMatcher:

    def save(

        self,

        screenshot,

        template,

        output_path="heatmap.png"

    ):

        result = cv2.matchTemplate(

            screenshot,

            template,

            cv2.TM_CCOEFF_NORMED

        )

        normalized = cv2.normalize(

            result,

            None,

            0,

            255,

            cv2.NORM_MINMAX

        )

        normalized = normalized.astype(

            "uint8"

        )

        cv2.imwrite(

            output_path,

            normalized

        )

        return output_path