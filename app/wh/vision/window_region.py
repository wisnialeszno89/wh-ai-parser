from dataclasses import (
    dataclass
)

from app.wh.vision.region import (
    Region
)


@dataclass
class WindowRegion(

    Region

):

    title: str = ""