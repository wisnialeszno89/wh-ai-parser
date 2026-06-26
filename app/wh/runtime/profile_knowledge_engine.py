from app.wh.runtime.profile_knowledge import (
    PROFILE_KNOWLEDGE
)


class ProfileKnowledgeEngine:

    def get(

        self,

        system

    ):

        return (

            PROFILE_KNOWLEDGE.get(

                system,

                {}

            )

        )