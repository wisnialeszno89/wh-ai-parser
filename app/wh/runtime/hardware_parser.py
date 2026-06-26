from app.wh.runtime.features.hardware_package import (
    HardwarePackage
)

from app.wh.runtime.hardware_registry import (
    HIDDEN_HINGE_ALIASES,
    V_PERFECT_ALIASES
)


class HardwareParser:

    def parse(

        self,

        text

    ):

        lower = (

            text.lower()

        )

        hardware = (

            HardwarePackage()

        )

        hardware.hidden_hinges = any(

            alias in lower

            for alias in HIDDEN_HINGE_ALIASES

        )

        hardware.v_perfect = any(

            alias in lower

            for alias in V_PERFECT_ALIASES

        )

        return hardware