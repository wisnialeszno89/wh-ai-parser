class GUIStateHistory:

    def __init__(

        self

    ):

        self.history = []

    def remember(

        self,

        snapshot

    ):

        self.history.append(

            snapshot

        )

    def last(

        self

    ):

        if not self.history:

            return None

        return (

            self.history[-1]

        )

    def count(

        self

    ):

        return len(

            self.history

        )