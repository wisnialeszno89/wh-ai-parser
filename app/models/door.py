from pydantic import BaseModel
from typing import Optional


class Door(BaseModel):

    enabled: bool = False

    threshold: bool = False

    opening_side: Optional[str] = None

    opening_direction: Optional[str] = None

    handle_type: Optional[str] = None

    lock_type: Optional[str] = None

    panel_type: Optional[str] = None