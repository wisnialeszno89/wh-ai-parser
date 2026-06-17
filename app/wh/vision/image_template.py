from dataclasses import dataclass

import numpy as np


@dataclass
class ImageTemplate:

    name: str

    image: np.ndarray