"""Exact WindowHub hardware-toolbar icon template.

The source image is a clean crop of the user-provided WindowHub screenshot,
without the red annotation circle. Keeping the tiny template embedded here
avoids a missing-file dependency while the hardware resolver is being
stabilized.
"""

from base64 import b64decode

import cv2
import numpy as np


_HARDWARE_ICON_PNG = (
    "iVBORw0KGgoAAAANSUhEUgAAAB4AAAAmCAYAAADTGStiAAACiklEQVR4nO2Xz2sTQRTHP/srVWxNQmzZUDCxeCiF2iqWRD0J0oJ4FMSj+Ed49C/wP/Hm1WMvKZqDaGwwpiZQNriCqS3pbtmZ8WBSkzRpdktElHxh2ZnZ995n3sCbmdUODgMlhETKzqMIAvG7LxRCSoQQSKmQQiLa30TQfnfbCtHu/7KVUhIIgRSqiyHR+UuagP9/sPmlWsYyzdAOOqDr7cYJNw0w8X2fb99HgC3TxJ6/MtZymrs0BfingzuND+/ekEwmQ2WtAQZgdGWslOLHQfiVO7ZMJpM4joNpWaGdewIZBp7nMXU+HQ0MYFoWm28r1Gp1BEaPoa4kuqYI+sYBEvE4Tx/dw2k0wk+0f2CntsvDB3cxNUV2YYHp6RkAPpbec3R0xMrqjRNBnj1/ERo4FKyA1ZVrzKXilMtlal8dstksyfgMiUQCFXjYtt3rpGmRwUPrWNM0FhcXWVtbo1gs0mq1SCQS1Gq1yJBI4I583yedTpPP53Ech2azSaVS+fPgUqnE0tLS8Qqsr6+zvb3N1tYWe3t7ZwafWnie52EYBlZXiWmaxvLyMrFYDMdxKJfL6JqMDD414062/cpkMtTrdVKpVPtQHyN4ULYdua5Ls9mkXq+Tz+cJVPgdayR4ULau61IoFNjf32djY4MgCCIDOxo4Vd/3e7J1XZdqtcrs7Cy5XO7YzrZtGhF2q5Hg6udP3LmVGwrsKJPJUCgUxgPWlcQ79CgWi0OB3bJtG4PoS34CnLh4gZevXhMQCx3knDV1drBSCtMwePL4fuQgHf8zgecvX6XR2Ix0tPVLj3BY9Cz19Zu3x3L1CQX2fZ/G7k74rBh92Wu1WjDgwtBjOfl3moAn4An4nwKbpsVP3snpJxKOLZgAAAAASUVORK5CYII="
)


def load_hardware_icon_template() -> np.ndarray:
    """Return the clean Okucia toolbar icon as a BGR OpenCV image."""
    raw = b64decode(_HARDWARE_ICON_PNG)
    image = cv2.imdecode(np.frombuffer(raw, dtype=np.uint8), cv2.IMREAD_COLOR)
    if image is None:
        raise RuntimeError("Unable to decode embedded hardware icon template")
    return image.copy()
