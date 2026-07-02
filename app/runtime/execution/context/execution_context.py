from dataclasses import dataclass


@dataclass
class ExecutionContext:

    screenshot: object | None = None

    templates_dir: str = ""

    mouse_enabled: bool = False

    debug: bool = True