from copy import deepcopy

from app.wh.runtime.profile_knowledge_engine import (
    ProfileKnowledgeEngine
)


class ProfileOptimizer:

    def __init__(

        self

    ):

        self.knowledge_engine = (

            ProfileKnowledgeEngine()

        )

    def optimize(

        self,

        offer

    ):

        optimized = (

            deepcopy(

                offer

            )

        )

        knowledge = (

            self.knowledge_engine.get(

                offer.profile.system

            )

        )

        if not knowledge:

            return optimized

        available = (

            knowledge[

                "glass_packages_mm"

            ]

        )

        if (

            optimized.glass.thickness_mm

            not in available

        ):

            optimized.glass.thickness_mm = (

                max(

                    available

                )

            )

        return optimized