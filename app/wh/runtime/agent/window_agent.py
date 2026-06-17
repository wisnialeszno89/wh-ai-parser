from app.wh.runtime.query.query_resolver import (
    QueryResolver
)

from app.wh.runtime.schema.construction_schema_factory_v2 import (
    ConstructionSchemaFactoryV2
)

from app.wh.runtime.constructions.construction_engine import (
    ConstructionEngine
)

from app.wh.runtime.constructions.executors.construction_executor import (
    ConstructionExecutor
)


class WindowAgent:

    def __init__(

        self

    ):

        self.query_resolver = (

            QueryResolver()

        )

        self.schema_factory = (

            ConstructionSchemaFactoryV2()

        )

        self.construction_engine = (

            ConstructionEngine()

        )

        self.construction_executor = (

            ConstructionExecutor()

        )

    def execute(

        self,

        text

    ):

        query = (

            self.query_resolver.resolve(

                text

            )

        )

        schema = (

            self.schema_factory.create(

                pattern=query.pattern,

                width=query.width,

                height=query.height

            )

        )

        construction = (

            self.construction_engine.build(

                schema

            )

        )

        self.construction_executor.execute(

            construction

        )

        return True