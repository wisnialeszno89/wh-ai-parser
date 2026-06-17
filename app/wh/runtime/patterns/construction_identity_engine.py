from app.wh.runtime.patterns.hst_recognizer import (
    HSTRecognizer
)

from app.wh.runtime.patterns.psk_recognizer import (
    PSKRecognizer
)


class ConstructionIdentityEngine:

    def __init__(

        self

    ):

        self.recognizers = [

            HSTRecognizer(),

            PSKRecognizer()

        ]

    def identify(

        self,

        reasoning

    ):

        for recognizer in (

            self.recognizers

        ):

            if recognizer.matches(

                reasoning

            ):

                return (

                    recognizer.name()

                )

        return "UNKNOWN"