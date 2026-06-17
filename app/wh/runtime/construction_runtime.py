from app.wh.runtime.patterns.construction_identity_engine import (
    ConstructionIdentityEngine
)

from app.wh.runtime.engines.engine_factory import (
    EngineFactory
)


class ConstructionRuntime:

    def __init__(

        self

    ):

        self.identity_engine = (

            ConstructionIdentityEngine()

        )

        self.factory = (

            EngineFactory()

        )

    def execute(

        self,

        reasoning,

        construction

    ):

        identity = (

            self.identity_engine

            .identify(

                reasoning

            )

        )

        engine = (

            self.factory.create(

                identity

            )

        )

        return engine.execute(

            construction

        )