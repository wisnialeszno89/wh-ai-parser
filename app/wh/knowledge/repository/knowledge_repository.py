import json

from pathlib import Path

from app.wh.knowledge.models.profile import Profile


class KnowledgeRepository:

    def __init__(self):

        data = (

            Path(__file__).parent.parent

            / "data"

            / "profiles.json"

        )

        with open(

            data,

            encoding="utf-8"

        ) as fp:

            raw = json.load(fp)

        self._profiles = [

            Profile(

                manufacturer=item["manufacturer"],

                system=item["system"],

                security=item["security"],

                glazing=item["glazing"],

                colors=item["colors"]

            )

            for item in raw

        ]

    def profiles(

        self

    ) -> list[Profile]:

        return self._profiles