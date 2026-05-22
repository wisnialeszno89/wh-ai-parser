from dataclasses import dataclass


@dataclass
class ScreenshotRecord:

    name: str

    tool: str

    retry: int