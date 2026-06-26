from app.wh.knowledge.models.decision import Decision

from app.wh.knowledge.repository.knowledge_repository import (
    KnowledgeRepository
)


class KnowledgeEngine:

    def __init__(self):

        self.repository = (

            KnowledgeRepository()

        )

    def choose_profile(

        self,

        security,

        glazing

    ) -> Decision:

        for profile in self.repository.profiles():

            if (

                security in profile.security

                and

                glazing in profile.glazing

            ):

                return Decision(

                    profile=profile.system,

                    confidence=1.0,

                    explanation=(
                        f"{profile.system} supports "
                        f"{security} and {glazing}"
                    )

                )

        return Decision(

            confidence=0.0,

            explanation="No matching profile found."

        )