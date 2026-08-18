"""Robust MVP selector for the WindowHub hardware dialog.

The live dialog screenshot showed that generic template matching was unstable:
the tree glyph and nearby text could beat the intended row. This version uses
an exact title-bar anchor from the real dialog to establish dialog origin, then
uses exact live crops for the selectable text and OK button. Relative geometry
is a fallback when the text/button crop is temporarily degraded.
"""

from __future__ import annotations

from base64 import b64decode
from dataclasses import dataclass

import cv2
import numpy as np


_TITLE_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAPoAAAAeCAYAAAAFOQOpAAAI7klEQVR4nO1cXUwURxz/HVIPlQu89QMRDptGbUAMEjggtQU0PmgVUJvU1Nhq2icVJNXUiMTW+oG9cuhDowVD2rSJCNr60JiekNpwB6Y2rW2a9oVy9kEbfQBDdTmMt304dm93b/ZuP2b2FuWXbNid3fnNfz5+M/OfmcPR0tLCQwGe5zU9J/tuFvoxW4azYAHH1NQUL21cShEr/0YikaTf6IHVDfvEiRPYv3+/aZ6nXZBtbW3Yt2+f+Py0l4eVMFLW6SQC0t9IJBIXRlPwVoKGfXbPIwlCHdLievz4MTW+VGAm1qFRpOsduZOFSZ9TDZIdT0IDNQra9WJVPdulPc1kpANycUufpfckQQtx7Dqiq9lhF/tIsLNtUljZoc+UMrEKhqfuWkdq6X0kEsHk5CTGxsbAcRwePnyIqakpKhmhBbUCuXnzpsWW2AO0BSMtx1kx2hsOjuN4ILmwhXthBL937x5u376D517Iwfz5mZi/IBNz5zpTlA07IdbgHcRQORzEUFqi0c5DtsMYlz7IedXs4OO+YdmxsO60ovzJy9wcvxQOjuP4RAJXTtF5nsfIyAjS5jyD3LwCOJ0ZzMy1P9QbhLIStTYdB0ORO1TfyN9r5aMDcseoNQ4bmOVPVMLWixwgLMYJ98qVduG6e/cu0uY8gxdfWsbM1JkBfY0hVsX0OGnCWpEbETcLsMuX2vtU5TcNiPfL1UZ2juNw586/yM0rILM5kOqasw2UVU5qAg7Cxdoma7sSXuUyy0nLHppIzpdKaYj76KTRW7myOjY2hmefzyFP1x2E+ydyfUZ7pniQR3K79IVs7bBbw0+tT29NXtXtSNOyDx6JRBCJRMBxHBYsyIxnUcvFEzfCGzj5x5DbDNj6w4njGG8WRssodSK3TgKJ7UhX2w+VLr4J14MHDzCfJHRWsNXMgIYRgo9mdKlOezr24onBeKOfmSK3Kq1kEKfuygU4Eh49emTtFpotBG4c6hU9E6aR9Edy6Rf6RMDGFnOwsnGaTytdudou/JVe0tNvjOywMYxlLtX+LwnxNsXvThvnt2afnV0cuvz06p9OXsSTcSQxqx2coQZte07auQSY5jRHYJdDMFIkFrnwbLRCjK1dpO6QjhlYOV2nhzQWpA1169DX2yMLW1G0VBYWCo0iO9OZsGSyXcndhOGhgKbvtKCvtwfNTbsMx19RtAwXFfkmYWgoiCzXPIRCozpTYN1Z2EFYZre/WM4srPbJ6eVFv9BJm7+K682t2xAMDIpRQqFRjI7+LQv7+cZP2LHzPVPGA8DJtmMYnwhTKhP9h2CEq8PnxWdnPkfDps0EnthzcdHLONl2nLltSjtp8NBE7Bgry71tI2Cx96/k1vIdXaQn/0Q/SlaW4siHreKzIOqBfr8YFgwMoqKqylQ6odAovO2nYwEWthNl711W5oHH45GEkI359bc/AABZrnk6UtPfAdHg0Qb9nOzPqhsBC3dNjT+R48KmXJhM3fPdbgAQp6Zff/UFNm95QxY20O9HSUkpmht3o7lptxg3FBrFiqKl4nNfbw+yXU5ku5zo8Hll3xUXLkFx4ZK4dyuKlqLD50W2y4nhoUCcfQ1160ROaVpSRNPNwPBQEM1Nu2Vuh/K5vm491q6pRpZrHny+T9HXewH1da9rL7CE0F7xifdsUy+smH2pt4UWtO2Tk/JrbRkwEToAVNesxs83fgIA9F/1o9xTKYYJYs93u7FrT5NspP/2m4s4eOiw+BwMDGJ8IozxiTBaWw6Iwi0uXIIr3w+I77rPdcrE98+tWxifCKPcUymzq7lpN/LzC8R429/ZiYa6dZAW/PBQEDve3obxiUmUeyoS5rO+bj1eWfUq7k9wuD/BobFxr7ECI0KfyGnw6EOMV/sxXjuKnGxTsvyY98mtc12YTN0BoKKqCsHBQeTk5KCmdnU0rLIq6qc7oh0BEBV7weLFGB4KoNxTie5znfjltz9FHm/7KfH+8EdHcf36MACgpna1TMQHDx1GMDCIhk1bAAC79jQRrOIx0O/HpcvfiSF7GpvR2nJAfA6FRrF2TTXGJybjTvWSKrb/qh8XL12WhTVs2jztq5uBvkrXtopNC/G2JUuf3UhullPbVpnyK3ZnEdgg/ejRowDi99CVYQLKKl6VM6jkuGHTFuzY/hYW5eXhza3bAMh9d6l//v7+D3Dh/HkAsQ5ADQsX5qq+W5SXlzBuDELvGa1Ctzv2I52/R0YAREd1T5LRnB20NRDljiIpFr2fvWqHUhj2E7n+fXD9nah9RA7wSDsWbsCxyXocD9fj+GQ9ToTr0RauQ1t4I06GN+JkeAM+CW/EJ+EN8D9aTuJQzVNN7Wp0n+tEycpSwBHz3bs6z6KkpFT8rtxTiYF+Py70nBd9eQF9vT2AIzrStrYcQMnKUpRXVKL/ql/mfx/5sBVlZeVJs1xdU4vTHe2i8R0+L6pramXvb/7+J9auqRZdjEV5eQhIdgy6Os/K8ujzfaqwWY+Pbmz6pr5XL7/oNzd1RqW42frkbERO52y6nUQeBTMfHQBeWfUagJjAgeiI7XYXyMIAYPs7OzHQ74/zqYOBQWRnOlFcuARd3V+K8X79/S+sXVMtLqodPHQ4Lq4c0cL3tp+K7uG7MpDtysCP136QuQcAkJ/vxpXvB7C8cCl8Pi8aG5vR1XkWWa4MZLkysGPnu9OMPPouXUb3uS5kueaJi3HaQbNBsGxc2johtgeFWHPa97CLOUTLyoG9N3jw05XIT7/gI9N/5eHL00K49vEWaXxMs5hGR7sXC3NzRR9bRx6ofWhkIcm4b0xvOyfRuM3+THmitMzwWd9BmGvGVo3iidJR/xWY8cU4yt1fa8sBjP8XpksKwLzIWTQOY42C/Js39RVjfdDut2qzflbk9JEsHfX3TKfuShNIk7+Odi+yM53o6v6SQUpsRW7Mnpkncv1+q9181MQznidD5IlhfOpuwkxqk4G4vBspDB4OokW0RE4H8UKnJfIomx4utVzRWXizbt3iaRC4AN1TdyFZvYXEfqGDp/iPKuwl8nhm66brWr82L3La5cV6cdIK0Evnf6Z//eQfTovQAAAAAElFTkSuQmCC"
)

_UR_B64 = "iVBORw0KGgoAAAANSUhEUgAAAHUAAAAKCAYAAACKcBGoAAACDUlEQVR4nO2WPXKjQBCFP3QWROCaE3ADpISIdLNRJpP4Bs42wcqkbFMiJ8AJlhOoFGi4S2+AsAcEGG9p15RLr4qi5qcfj+75ecgQTCK+n4jp6+uOmUR8tOSjXFq070ti7G5f6MTl2mqPaagbkticQ/pyLTRte6yPv9HV6s9Fg/ht8b2xc8CCW8D1UCPDVZZC9ESoStKsanrJUkjMnsCaG+zb7Q8+zDrindOcIFrjdqcFIbo8YSZxFvyMIfn1aPEE7E0CaUY1GDcf3KaoxSsH/4Fl72BdvGjtEoSasklMlZGWCu+qAp+D6ynKk7nIOKB6CKuX5xF93clnjn7EukvjeqjJC+NrsQDYbrfY70koY5aOg+M4OM8PmN+P1zsE6uJxSVIQosuUt806NdFjCEL04ZWCivNREzbb3NK3TKNhfd8QC4Ddbof9ngQ/wYgguYaRFVxlKeVbglccuBzBroeyC/zXCAj1kXORkarw/ehu9IkgnynokK7qzPEWi/A/YPj47fm5KksplddOULBHclg5G4orkoosLdH5JbmXRVAfwQFPCcTLdlyx6eMZRxAq4lWMCqffxiNsta4fL9b9WbBZxv339RwxaqNMIj4IzTPiGmsn23a3/Q4xF23Nq+Osb+h8OL6lx3bNuWg+cM198d3/szi6unTX2s/Y/ToiIl+znO74V7iN+71jVrgX9RviDyQIwL8B1L9UAAAAAElFTkSuQmCC"
_OK_B64 = "iVBORw0KGgoAAAANSUhEUgAAAFAAAAAjCAYAAAADp43CAAACuklEQVR4nO2aP2gTURjAf8lFSDuYNDYVSu0SElDapVvtdesQuM0hg4JBoRAcTjMIipODKDiEZigFwZI1gyB4kEWXpnbSpaHCaZZSAq1tvOBgbe9Sh9rrv6uCh7kLvB/ckPc9wseP773v8XgBwzD2EPwzQa8T6HaEQJcIgS4RAl0iBLpECHRJ6OiP1ZbFHa3J8sYure22Vzn5CiXZw9OpKMMRyTFuC1xtWUzOr3Nv4gKvszGiYVGcxnab0keDyZfrLNy+6CgxcHCQvvFqi6lkBPVqX8cT9TuP337l3ZfvvLkePxWzy0zTf3BzLNLRxLqFuxMxltd3HWPH1qlYts5EwxKtn849QRhziRDoEs8F1osykiTZn1ysHwSQ5SL1g4mVHJIkkat4lakzngqsF2VS5Qy6ZWFZFpalMZJPHUo8nIis1CjoFnNpb3I9Cw8FVnieh0JJJWGPpZnTC1DWDiuPCrlUmYxeRU04/Y+3eCewrlMbz6CclJJIMbK0wmcAymQlBTR/ygMf7IF/ZAkyhWleKDl8tvXZeCcwkWJkqYx2Yrvbr8wrJAHGMyjqHHqhhuK37vEbDyswzf0C5LPFE/tdHjIKR1dsQi1RqCmnm4sPCP19yv8joVbRkUlJeXtsWrOopoFjrhKoVY0VKYWMTtVHG6J9mRB9tob15LLX+fgW6dEnjAdDp8b93US6AFtgJBzEEJeojhjb1pkxW+DowDlmFpsdSajbKH1ooSR7HGN2E5lV+pic3yDaEyQ7FhVXW+zfSM8sbjHzvsnCrQHHOYGjTztWWyYPtTW0lW+wJ158RMISo0Pnmb12ieGI84ElIN7GuEOsU5cIgS4RAl0iBLrkWGsxTZPNzU12dnZot8WhGqC3t5dYLEYo5NyF7VHTNGk0GsTjcfr7+wkGRXG2222azSaNRoPBwUFHib8AuCLe2SPtldwAAAAASUVORK5CYII="

@dataclass(frozen=True)
class HardwareSelectionTarget:
    name: str
    point: tuple[int, int]
    confidence: float

class HardwareSelectionResolver:
    SCALE_FACTORS = (0.90, 0.95, 1.0, 1.05, 1.10)
    MIN_TITLE_CONFIDENCE = 0.90
    MIN_TARGET_CONFIDENCE = 0.90

    # With the exact live dialog anchor, these are measured from the title crop's
    # top-left. The title crop matched at (450,100) on the supplied live screen;
    # UR center was (566,209) and OK center was (1370,528).
    UR_OFFSET = (116, 109)
    OK_OFFSET = (920, 428)

    def __init__(self) -> None:
        self._title = self._decode(_TITLE_B64)
        self._ur = self._decode(_UR_B64)
        self._ok = self._decode(_OK_B64)

    @staticmethod
    def _decode(payload: str) -> np.ndarray:
        image = cv2.imdecode(np.frombuffer(b64decode(payload), dtype=np.uint8), cv2.IMREAD_GRAYSCALE)
        if image is None:
            raise RuntimeError("Unable to decode embedded hardware selector template")
        return image

    @staticmethod
    def _gray(image: np.ndarray) -> np.ndarray:
        if image.ndim == 2:
            return image
        return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    def _match(self, image: np.ndarray, template: np.ndarray, region: tuple[int,int,int,int] | None = None):
        gray = self._gray(image)
        h, w = gray.shape[:2]
        if region is None:
            x1, y1, x2, y2 = 0, 0, w, h
        else:
            x1, y1, x2, y2 = region
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(w, x2), min(h, y2)
        roi = gray[y1:y2, x1:x2]
        best = None
        for scale in self.SCALE_FACTORS:
            tw = max(1, int(round(template.shape[1] * scale)))
            th = max(1, int(round(template.shape[0] * scale)))
            if tw > roi.shape[1] or th > roi.shape[0]:
                continue
            resized = cv2.resize(template, (tw, th), interpolation=cv2.INTER_AREA if scale < 1 else cv2.INTER_CUBIC)
            result = cv2.matchTemplate(roi, resized, cv2.TM_CCOEFF_NORMED)
            _, score, _, loc = cv2.minMaxLoc(result)
            cand = (float(score), (x1 + loc[0], y1 + loc[1], tw, th), scale)
            if best is None or cand[0] > best[0]:
                best = cand
        return best

    def _dialog_anchor(self, image: np.ndarray):
        # Dialog is centered in the application; exclude the document table edge
        # and bottom notes pane to reduce false matches.
        h, w = image.shape[:2]
        return self._match(image, self._title, (0, 0, w, int(h * 0.35)))

    def find_ur_activpilot(self, image: np.ndarray) -> HardwareSelectionTarget | None:
        anchor = self._dialog_anchor(image)
        if anchor and anchor[0] >= self.MIN_TITLE_CONFIDENCE:
            ax, ay, _, _ = anchor[1]
            scale = anchor[2]
            # Exact crop match first, constrained to the left tree area.
            region = (ax, ay + int(50 * scale), ax + int(550 * scale), ay + int(310 * scale))
            result = self._match(image, self._ur, region)
            if result and result[0] >= self.MIN_TARGET_CONFIDENCE:
                score, (x, y, w, h), _ = result
                point = (x + w // 2, y + h // 2)
                print(f"[HARDWARE SELECT] title anchor conf={anchor[0]:.3f} at=({ax},{ay})")
                print(f"[HARDWARE SELECT] UR ACTIVPILOT exact conf={score:.3f} box=({x},{y},{w}x{h}) click={point}")
                return HardwareSelectionTarget("UR ACTIVPILOT", point, score)

            point = (ax + int(self.UR_OFFSET[0] * scale), ay + int(self.UR_OFFSET[1] * scale))
            print(f"[HARDWARE SELECT] UR ACTIVPILOT relative fallback click={point}")
            return HardwareSelectionTarget("UR ACTIVPILOT", point, anchor[0])

        print("[HARDWARE SELECT] dialog title anchor not found")
        return None

    def find_ok(self, image: np.ndarray, after: HardwareSelectionTarget | None = None) -> HardwareSelectionTarget | None:
        anchor = self._dialog_anchor(image)
        if anchor and anchor[0] >= self.MIN_TITLE_CONFIDENCE:
            ax, ay, _, _ = anchor[1]
            scale = anchor[2]
            region = (ax + int(700 * scale), ay + int(300 * scale), min(image.shape[1], ax + int(1000 * scale)), min(image.shape[0], ay + int(570 * scale)))
            result = self._match(image, self._ok, region)
            if result and result[0] >= self.MIN_TARGET_CONFIDENCE:
                score, (x, y, w, h), _ = result
                point = (x + w // 2, y + h // 2)
                print(f"[HARDWARE SELECT] OK exact conf={score:.3f} box=({x},{y},{w}x{h}) click={point}")
                return HardwareSelectionTarget("OK", point, score)

            point = (ax + int(self.OK_OFFSET[0] * scale), ay + int(self.OK_OFFSET[1] * scale))
            print(f"[HARDWARE SELECT] OK relative fallback click={point}")
            return HardwareSelectionTarget("OK", point, anchor[0])

        print("[HARDWARE SELECT] dialog title anchor not found for OK")
        return None

    def resolve(self, image: np.ndarray):
        return self.find_ur_activpilot(image), self.find_ok(image)
