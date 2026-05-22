import json


class ActionPipeline:

    def __init__(self):

        self.actions = []

    def add(

        self,
        action
    ):

        self.actions.append(
            action
        )

    def run(

        self,
        runtime
    ):

        for action in self.actions:

            action.execute(
                runtime
            )

    def serialize(self):

        return [

            action.serialize()

            for action in self.actions
        ]

    def export(

        self,
        path
    ):

        with open(

            path,

            "w",

            encoding="utf-8"
        ) as file:

            json.dump(

                self.serialize(),

                file,

                indent=4
            )

        print(
            f"[PIPELINE] exported "
            f"{path}"
        )