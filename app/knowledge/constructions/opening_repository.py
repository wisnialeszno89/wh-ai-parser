import json

from pathlib import Path

from app.knowledge.constructions.models.opening_definition import (
    OpeningDefinition
)


class OpeningRepository:

    DATA_PATH = Path(
        "app/knowledge/constructions/data/openings.json"
    )

    def load_all(self):

        with open(
            self.DATA_PATH,
            encoding="utf-8"
        ) as file:

            data = json.load(file)

        return [

            OpeningDefinition(**item)

            for item in data
        ]