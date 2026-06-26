from app.wh.runtime.vision.mail_recognizer import (
    MailRecognizer
)

from app.wh.runtime.vision.requirement_extractor import (
    RequirementExtractor
)

from app.wh.runtime.vision.offer_expert import (
    OfferExpert
)


class MailToOfferPipelineV2:

    def __init__(self):

        self.mail_recognizer = MailRecognizer()

        self.requirement_extractor = RequirementExtractor()

        self.offer_expert = OfferExpert()

    def execute(

        self,

        subject: str,

        body: str

    ):

        recognition = (

            self.mail_recognizer.recognize(

                body

            )

        )

        requirements = (

            self.requirement_extractor.extract(

                recognition.body

            )

        )

        requirements.language = (

            recognition.metadata.language

        )

        return (

            self.offer_expert.build_offer(

                requirements

            )

        )