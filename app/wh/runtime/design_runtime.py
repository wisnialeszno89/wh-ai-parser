from app.wh.runtime.design_engine import (
    DesignEngine
)

from app.wh.runtime.design_compiler import (
    DesignCompiler
)

from app.wh.runtime.constructions.construction_engine import (
    ConstructionEngine
)

from app.wh.runtime.construction_executor import (
    ConstructionExecutor
)


class DesignRuntime:

    def __init__(

        self

    ):

        self.design_engine = (

            DesignEngine()

        )

        self.compiler = (

            DesignCompiler()

        )

        self.construction_engine = (

            ConstructionEngine()

        )

        self.executor = (

            ConstructionExecutor()

        )

    def execute(

        self,

        project

    ):

        report = (

            self.design_engine.design(

                project

            )

        )

        schema = (

            self.compiler.compile(

                project,

                report.winner

            )

        )

        construction = (

            self.construction_engine.build(

                schema

            )

        )

        self.executor.execute(

            construction

        )

        return construction