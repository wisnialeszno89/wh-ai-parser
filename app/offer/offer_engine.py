from app.agent.agent import Agent


class OfferEngine:

    def process(
        self,
        offer
    ):

        reports = []

        agent = Agent()

        for position in offer.positions:

            report = agent.run(
                position.context
            )

            reports.append(report)

        return reports