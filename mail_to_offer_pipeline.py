from app.wh.runtime.vision.mail_to_offer_result import (
    MailToOfferResult
)


class MailToOfferPipeline:

    def execute(

        self,

        mail

    ):

        return (

            MailToOfferResult(

                success=True

            )

        )