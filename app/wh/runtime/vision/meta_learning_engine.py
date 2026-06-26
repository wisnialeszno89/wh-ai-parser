class MetaLearningEngine:

    def learn(

        self,

        strategy,

        brain

    ):

        brain.meta_learning_memory.remember(

            strategy

        )