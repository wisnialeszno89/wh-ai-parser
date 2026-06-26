class RecoveryLearningEngine:

    def learn(

        self,

        reason,

        strategy,

        brain

    ):

        brain.recovery_learning_memory.remember(

            reason,

            strategy

        )