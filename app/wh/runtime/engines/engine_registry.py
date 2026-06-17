from app.wh.runtime.engines.hst_engine import (
    HSTEngine
)

from app.wh.runtime.engines.psk_engine import (
    PSKEngine
)


class EngineRegistry:

    def __init__(

        self

    ):

        self.engines = {

            "HST":

            HSTEngine(),

            "PSK":

            PSKEngine()

        }

    def get(

        self,

        identity

    ):

        if identity not in self.engines:

            raise Exception(

                f"Unknown identity: {identity}"

            )

        return self.engines[

            identity

        ]