from pydantic import BaseModel


class Mullion(BaseModel):

    type: str

    movable: bool = False

    width_mm: int = 0