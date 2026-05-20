from pydantic import BaseModel
from typing import Optional


class RollerShutter(BaseModel):

    enabled: bool = False

    type: Optional[str] = None
    # external
    # top_mounted

    box_size_mm: Optional[int] = None

    motorized: bool = False

    motor_side: Optional[str] = None