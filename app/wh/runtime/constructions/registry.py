from app.wh.runtime.constructions.fix_ru_builder import (
    FixRuBuilder
)


class ConstructionRegistry:

    BUILDERS = {

        "FIX": FixRuBuilder(),

        "FIX_RU": FixRuBuilder()
    }

    @classmethod
    def resolve(

        cls,
        geometry
    ):

        if geometry not in cls.BUILDERS:

            raise RuntimeError(

                f"Unknown geometry: "
                f"{geometry}"
            )

        return cls.BUILDERS[
            geometry
        ]