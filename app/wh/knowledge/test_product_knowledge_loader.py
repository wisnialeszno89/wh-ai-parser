from app.wh.knowledge.product_knowledge_loader import (
    ProductKnowledgeLoader
)


def test_product_knowledge_loader():

    loader = (

        ProductKnowledgeLoader()

    )

    data = (

        loader.load_manufacturer(

            "veka_softline82"

        )

    )

    assert (

        data["manufacturer"]

        ==

        "VEKA"

    )

    assert (

        "RAL7016"

        in

        data["colors"]

    )