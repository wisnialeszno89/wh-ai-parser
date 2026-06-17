import cv2
import numpy as np


class TemplateLoader:

    def load(

        self,

        path

    ):

        return self._load(

            path

        )

    def _load(

        self,

        path

    ):

        image = (

            cv2.imread(

                path

            )

        )

        if image is None:

            return np.zeros(

                (

                    50,

                    50,

                    3

                ),

                dtype=np.uint8

            )

        return image