from app.wh.vision.window_locator import WindowLocator


class WindowAnalyzer:
    """
    Responsible for locating the active application window.

    This is currently a thin wrapper around WindowLocator.
    In the future it may support multiple detection strategies.
    """

    def __init__(self):

        self._locator = WindowLocator()

    def analyze(self):

        print("[VISION] Analyze window")

        window = self._locator.locate()

        if window is None:
            raise RuntimeError("Application window not found.")

        print(f"[VISION] Window: {window}")

        return window