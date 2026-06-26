from app.wh.runtime.configuration_problem import (
    ConfigurationProblem
)

from app.wh.runtime.profile_knowledge_engine import (
    ProfileKnowledgeEngine
)


class ProfileReasoningEngine:

    def __init__(

        self

    ):

        self.knowledge_engine = (

            ProfileKnowledgeEngine()

        )

    def validate(

        self,

        offer

    ):

        problems = []

        knowledge = (

            self.knowledge_engine.get(

                offer.profile.system

            )

        )

        if not knowledge:

            return problems

        if (

            offer.glass.thickness_mm

            not in

            knowledge[

                "glass_packages_mm"

            ]

        ):

            problems.append(

                ConfigurationProblem(

                    code="INVALID_GLASS_PACKAGE",

                    message=(

                        f"Pakiet "

                        f"{offer.glass.thickness_mm} mm "

                        f"nie jest dostępny dla "

                        f"{offer.profile.system}"

                    )

                )

            )

        if (

            offer.hardware.hidden_hinges

            and

            not knowledge[

                "supports_hidden_hinges"

            ]

        ):

            problems.append(

                ConfigurationProblem(

                    code="HIDDEN_HINGES_NOT_SUPPORTED",

                    message=(

                        "Ukryte zawiasy "

                        "nie są dostępne"

                    )

                )

            )

        if (

            offer.security.rc2

            and

            not knowledge[

                "supports_rc2"

            ]

        ):

            problems.append(

                ConfigurationProblem(

                    code="RC2_NOT_SUPPORTED",

                    message=(

                        "RC2 nie jest dostępne"

                    )

                )

            )

        return problems