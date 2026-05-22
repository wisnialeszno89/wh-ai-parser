from app.wh.runtime.geometry.fix_geometry import (
    build_fix_geometry
)


class GeometryFactory:

    @staticmethod
    def build(intent):

        if intent.geometry == "FIX":

            return build_fix_geometry()

        raise RuntimeError(
            f"No geometry for "
            f"{intent.geometry}"
        )