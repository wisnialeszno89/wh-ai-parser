from app.agent.agent import Agent

from app.context.offer_context import (
    OfferContext
)


def main():

    context = OfferContext()

    context.construction_type = (
        "single_window"
    )

    report = Agent().run(
        context
    )

    print()

    print("=" * 40)

    print("AI WINDOW ENGINE")

    print("=" * 40)

    print()

    print("Construction Plan")

    print()

    for index, step in enumerate(

        report.construction_plan.steps,

        start=1

    ):

        print(

            f"{index}. {step.action}"

        )

    print()

    print("=" * 40)

    print("REPORT")

    print("=" * 40)

    print()

    print(

        f"Completed: "

        f"{report.completed_positions}"

    )

    print(

        f"Review: "

        f"{len(report.review_positions)}"

    )

    print()

    for message in report.messages:

        print(message)


if __name__ == "__main__":

    main()