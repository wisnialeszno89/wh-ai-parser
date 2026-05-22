from app.wh.runtime.geometry.geometry_map import (
    GeometryMap
)


class GeometryFactory:

    @staticmethod
    def build(intent):

        return GeometryMap()