from dataclasses import dataclass

from app.wh.vision.image_size import (
    ImageSize
)


@dataclass
class Image:

    file_name: str

    size: ImageSize