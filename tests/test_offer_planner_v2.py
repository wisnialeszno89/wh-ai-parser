from app.knowledge.offer.offer_parser import (
    parse_offer
)

from app.knowledge.planner.offer_planner import (
    plan_offer
)


def test_plan_offer_v2():

    text = """

1500x1400 FIX RU FIX

antracyt / biały

Veka Softline 82

Ug 0.5

nawiewnik Aereco

"""

    draft = parse_offer(
        text
    )

    result = plan_offer(
        draft
    )

    assert len(
        result.steps
    ) == 5

    assert (

        result.steps[0]
        .action

        ==

        "create_construction"

    )