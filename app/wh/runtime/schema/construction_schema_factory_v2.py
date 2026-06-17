from app.wh.runtime.patterns.pattern_parser import (
    PatternParser
)

from app.wh.runtime.schema.pattern_schema_builder import (
    PatternSchemaBuilder
)


class ConstructionSchemaFactoryV2:

    def __init__(

        self

    ):

        self.parser = PatternParser()

        self.builder = PatternSchemaBuilder()

    def create(

        self,

        pattern,

        width,

        height

    ):

        lines = [

            line.strip()

            for line in pattern.splitlines()

            if line.strip()

        ]

        pattern = "/".join(

            lines

        )

        rows = self.parser.parse(

            pattern

        )

        return self.builder.build(

            rows,

            width,

            height

        )