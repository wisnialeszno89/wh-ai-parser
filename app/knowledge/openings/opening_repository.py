import json

from pathlib import Path

from app.knowledge.openings.opening_definition import (
    OpeningDefinition
)


class OpeningRepository:

    DATA_PATH = Path(
        "app/knowledge/openings/openings.json"
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

            OpeningDefinition(**item)

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