from app.wh.runtime.vision.offer_agent import (
    OfferAgent
)


class ProjectAgent:

    def __init__(

        self,

        runtime

    ):

        self.offer_agent = (

            OfferAgent(

                runtime

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