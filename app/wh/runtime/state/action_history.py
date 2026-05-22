class ActionHistory:

    def __init__(self):

        self.items = []

    def add(

        self,
        action
    ):

        self.items.append(
            action
        )

    def print(self):

        print(
            "\n===== ACTION HISTORY ====="
        )

        for index, item in enumerate(

            self.items,

            start=1
        ):

            print(
                f"[{index}] {item}"
            )

        print(
            "==========================\n"
        )