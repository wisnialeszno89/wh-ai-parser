from pydantic import BaseModel


class MosquitoNet(BaseModel):

    enabled: bool = False

    type: str = "frame"