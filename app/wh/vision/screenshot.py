from dataclasses import dataclass

import numpy as np


@dataclass
class Screenshot:

    width: int

    height: int

    image: np.ndarray