class LearningEngine:

    def learn(

        self,

        brain

    ):

        for record in (

            brain.failure_history.records

        ):

            brain.learning_memory.remember(

                record.reason,

                record.goal

            )