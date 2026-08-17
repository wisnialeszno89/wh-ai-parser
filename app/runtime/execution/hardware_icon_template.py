import base64

import cv2
import numpy as np


# Cropped directly from the user-provided WindowHub screenshot.
# It is the actual "Okucia (F5)" toolbar button, not the old generic template.
_HARDWARE_ICON_PNG_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAABgAAAAcCAYAAAB75n/uAAACcUlEQVR4nNWWT2sTQRiHn9k/qWJrNsSWDQUTi4dSqK1iSdSTIC2IR0E8ih/Co5/Ab+LNq8deUjQH0djFmJpA2eAKpraku2V3xkOzNWmyTVrqoT9Ydnf2nd/zvrM7Myv29kMVRRIp40MRhtG/+0gRSUkURUipkJEk6j6Lwu65NzaKuveHsRr/WRcfYPyoO5iGMXYHDdC07sVANwEYBEHAr99dgGkY2LM3zvUlz1ybAIJDQMz+8ukDmUxmrCoEoAN6TwVKKf7sDY7EUUsmk8F1XQzTHAsyYKTr+L7PxOXccACAYZqsf6zRaDSJ0PsCNSXRhCI81g5gpdO8fPYIt9VKriDWVmObp08eYghFYW6OyckpAL5WP3NwcMDS8p0Bk1ev3yRXdrxBActLt5jJpnEch8ZPl0KhQCY9hWVZqNDHtu3+TkIkAhLngRCC+fl5VlZWqFQqdDodLMui0Wgkmp0KECsIAnK5HKVSCdd1abfb1Gq18wNUq1UWFhaOKlpdXWVzc5ONjQ12dnZGAk6cwr7vo+s6Zs+nK4RgcXGRVCqF67o4joMm5NkqiLM/rnw+T7PZJJvNIqVE4wyAYdnH8jyPdrtNs9mkVCoRquSBSAQMy97zPMrlMru7u6ytrRGGYaJxrKHoIAj6svc8j3q9zvT0NMVi8SjOtm1aQ2bvSED9+zce3CsmGsfK5/OUy+XTATQl8fd9KpVKonGvbNtGJ3moBgDW1Su8ffeekNSJxr26ZE6MBiilMHSdF88fj23cK6XUyYDZ6zdptdaHLrnjShuy6PUN0e27989ly+wDBEFAa3tr/CwZvel3Oh3obkziwv/Z/QUoqcVWgvKxyQAAAABJRU5ErkJggg=="
)


def load_hardware_icon_template() -> np.ndarray:
    data = base64.b64decode(_HARDWARE_ICON_PNG_B64)
    image = cv2.imdecode(np.frombuffer(data, dtype=np.uint8), cv2.IMREAD_COLOR)
    if image is None:
        raise RuntimeError("Unable to decode embedded hardware icon template")
    return image
