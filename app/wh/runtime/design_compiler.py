from app.wh.runtime.schema.construction_schema_factory_v2 import (
    ConstructionSchemaFactoryV2
)


class DesignCompiler:

    def __init__(

        self

    ):

        self.factory = (

            ConstructionSchemaFactoryV2()

        )

    def compile(

        self,

        project,

        candidate

    ):

        return (

            self.factory.create(

                candidate.notation,

                width=project.schema.width,

                height=project.schema.height

            )

        )