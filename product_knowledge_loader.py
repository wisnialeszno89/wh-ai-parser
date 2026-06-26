import json
from pathlib import Path


class ProductKnowledgeLoader:

    def load_manufacturer(

        self,

        name

    ):

        directory = (

            Path(__file__).parent

            / "manufacturers"

        )

        file = (

            directory

            / f"{name}.json"

        )

        with open(

            file,

            encoding="utf-8"

        ) as fp:

            return json.load(fp)