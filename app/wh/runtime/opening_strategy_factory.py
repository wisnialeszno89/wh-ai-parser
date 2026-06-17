from app.wh.model.opening import (
    Opening
)

from app.wh.runtime.fix_strategy import (
    FixStrategy
)

from app.wh.runtime.hst_strategy import (
    HSTStrategy
)

from app.wh.runtime.tilt_turn_strategy import (
    TiltTurnStrategy
)


class OpeningStrategyFactory:

    def create(

        self,

        opening

    ):

        if opening == Opening.FIX:

            return FixStrategy()

        if opening in (

            Opening.TURN,

            Opening.TILT,

            Opening.TILT_TURN

        ):

            return TiltTurnStrategy()

        if opening == Opening.HST:

            return HSTStrategy()

        raise RuntimeError(

            f"Unsupported opening: "

            f"{opening}"

        )