import json

from pathlib import Path

from app.knowledge.constructions.construction_definition import (
    ConstructionDefinition
)


class ConstructionRepository:

    DATA_PATH = Path(
        "app/knowledge/constructions/constructions.json"
    )

    def __init__(self):

        self._definitions = None

    def load(self):

        if self._definitions is not None:
            return

        with open(
            self.DATA_PATH,
            encoding="utf-8"
        ) as file:

            data = json.load(file)

        self._definitions = [

            ConstructionDefinition(**item)

            for item in data
        ]

    def get_by_code(
        self,
        code: str
    ):

        self.load()

        for definition in self._definitions:

            if definition.code == code:

                return definition

        return None