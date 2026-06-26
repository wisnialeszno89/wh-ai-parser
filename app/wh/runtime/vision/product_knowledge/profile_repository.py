import json

from pathlib import Path


class ProfileRepository:

    def __init__(self):

        file = (

            Path(__file__).parent

            / "data"

            / "profiles.json"

        )

        with open(

            file,

            encoding="utf-8"

        ) as fp:

            self._profiles = json.load(fp)

    def all(self):

        return self._profiles

    def find_matching(

        self,

        security,

        glazing

    ):

        result = []

        for profile in self._profiles:

            if (

                security in profile["security"]

                and

                glazing in profile["glazing"]

            ):

                result.append(

                    profile

                )

        return result