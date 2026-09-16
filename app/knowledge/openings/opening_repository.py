import json
import re

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

    def find_codes_in_text(
        self,
        text: str,
    ) -> list[str]:
        self.load()

        normalized = text.strip().lower()
        matches = []

        for definition in self._definitions:
            for alias in definition.aliases:
                alias_normalized = (
                    alias.strip().lower()
                )

                if not alias_normalized:
                    continue

                pattern = (
                    rf"(?<!\w)"
                    rf"{re.escape(alias_normalized)}"
                    rf"(?!\w)"
                )

                if re.search(
                    pattern,
                    normalized,
                ):
                    matches.append(
                        definition.code
                    )

        return list(dict.fromkeys(matches))

    def get_by_code_or_alias(
        self,
        value: str
    ):
        self.load()

        normalized = value.strip().lower()

        for definition in self._definitions:
            if definition.code.lower() == normalized:
                return definition

            if any(
                alias.lower() == normalized
                for alias in definition.aliases
            ):
                return definition

        return None
