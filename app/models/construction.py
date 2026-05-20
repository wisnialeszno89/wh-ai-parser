from pydantic import BaseModel
from typing import List
from typing import Optional

from app.models.segment import Segment
from app.models.roller_shutter import RollerShutter
from app.models.mosquito_net import MosquitoNet
from app.models.door import Door


class Construction(BaseModel):

    construction_id: int

    category: str

    width_mm: int

    height_mm: int

    segments: List[Segment]

    color_inside: str

    color_outside: str

    glass_type: str

    profile_system: str

    roller_shutter: Optional[RollerShutter] = None

    mosquito_net: Optional[MosquitoNet] = None

    door: Optional[Door] = None