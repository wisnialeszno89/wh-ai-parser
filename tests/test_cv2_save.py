import os
import cv2
import numpy as np


os.makedirs(
    "dataset/test",
    exist_ok=True
)

image = np.zeros(
    (24, 24),
    dtype=np.uint8
)

path = "dataset/test/test.png"

success = cv2.imwrite(
    path,
    image
)

print(success)

print(
    os.path.exists(path)
)