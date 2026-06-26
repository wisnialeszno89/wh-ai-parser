from app.wh.runtime.vision.recovery_knowledge import (
    RecoveryKnowledge
)


class RecoveryKnowledgeBase:

    def __init__(

        self

    ):

        self.knowledge = {}

    def remember(

        self,

        failure_reason,

        recovery_strategy,

        successful

    ):

        key = (

            failure_reason,

            recovery_strategy

        )

        if key not in self.knowledge:

            self.knowledge[key] = (

                RecoveryKnowledge(

                    failure_reason=(

                        failure_reason

                    ),

                    recovery_strategy=(

                        recovery_strategy

                    ),

                    success_count=0,

                    failure_count=0

                )

            )

        item = (

            self.knowledge[key]

        )

        if successful:

            item.success_count += 1

        else:

            item.failure_count += 1

    def get(

        self,

        failure_reason,

        recovery_strategy

    ):

        return (

            self.knowledge.get(

                (

                    failure_reason,

                    recovery_strategy

                )

            )

        )