from app.services.offer_pipeline import (
    build_offer_pipeline
)

from app.services.template_recommender import (
    recommend_template

)from app.services.construction_aliases import (
    normalize_construction_id
)


def build_ofr_offer(
    text: str
):

    results = build_offer_pipeline(
        text
    )

    output = []


    for item in results:

        schema = item[
            "schema"
        ]


        construction = item[
            "match"
        ][
            "construction"
        ]


        construction_id = normalize_construction_id(

        construction[
        "id"
    ]
)


        recommended = recommend_template(

            schema,

            construction_id
        )


        output.append({

            "schema":
                schema,

            "construction_id":
                construction_id,

            "recommended_template":
                recommended
        })


    return output