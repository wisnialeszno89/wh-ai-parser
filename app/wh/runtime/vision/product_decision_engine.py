from app.wh.runtime.vision.product_knowledge.profile_repository import (
    ProfileRepository
)


class ProductDecisionEngine:

    def __init__(

        self

    ):

        self.repository = (

            ProfileRepository()

        )

    def choose_profile(

        self,

        requirements

    ) -> str | None:

        profiles = (

            self.repository.find_matching(

                security=requirements.security,

                glazing=requirements.glazing

            )

        )

        if not profiles:

            return None

        return profiles[0]["system"]