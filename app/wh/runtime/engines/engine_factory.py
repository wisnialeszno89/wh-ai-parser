from app.wh.runtime.engines.engine_registry import (
    EngineRegistry
)


class EngineFactory:

    def __init__(

        self

    ):

        self.registry = (

            EngineRegistry()

        )

    def create(

        self,

        identity

    ):

        return self.registry.get(

            identity

        )