class EngineContext:

    def __init__(

        self,

        engine

    ):

        self.engine = engine

    def execute(

        self,

        construction

    ):

        return self.engine.execute(

            construction

        )

    def name(

        self

    ):

        return (

            self.engine

            .__class__

            .__name__

        )