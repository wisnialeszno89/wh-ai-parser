from app.wh.runtime.vision.intelligent_offer_agent import (
    IntelligentOfferAgent
)


class IntelligentProjectAgent:

    def __init__(

        self,

        runtime,

        brain

    ):

        self.offer_agent = (

            IntelligentOfferAgent(

                runtime,

                brain

            )

        )

    def execute(

        self,

        project

    ):

        self.offer_agent.execute(

            project.offer

        )

        return True