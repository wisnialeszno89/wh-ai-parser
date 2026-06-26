from dataclasses import (
    dataclass
)

from app.wh.vision.region import (
    Region
)


@dataclass
class ButtonRegion(

    Region

):

    label: str = ""