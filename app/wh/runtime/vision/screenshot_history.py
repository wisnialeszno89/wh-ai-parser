class ScreenshotHistory:

    def __init__(

        self

    ):

        self.history = []

    def remember(

        self,

        image

    ):

        self.history.append(

            image

        )

    def count(

        self

    ):

        return len(

            self.history

        )