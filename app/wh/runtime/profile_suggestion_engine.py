from app.wh.runtime.configuration_suggestion import (
    ConfigurationSuggestion
)

from app.wh.runtime.profile_knowledge_engine import (
    ProfileKnowledgeEngine
)


class ProfileSuggestionEngine:

    def __init__(

        self

    ):

        self.knowledge_engine = (

            ProfileKnowledgeEngine()

        )

    def suggest(

        self,

        offer

    ):

        suggestions = []

        knowledge = (

            self.knowledge_engine.get(

                offer.profile.system

            )

        )

        if not knowledge:

            return suggestions

        if (

            offer.glass.thickness_mm

            not in

            knowledge["glass_packages_mm"]

        ):

            available = (

                ", ".join(

                    str(x)

                    for x in knowledge["glass_packages_mm"]

                )

            )

            suggestions.append(

                ConfigurationSuggestion(

                    code="GLASS_PACKAGE_SUGGESTION",

                    message=(

                        f"Dostępne pakiety dla "

                        f"{offer.profile.system}: "

                        f"{available} mm"

                    )

                )

            )

        return suggestions