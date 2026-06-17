import json
import os


MEMORY_PATH = (
    "memory/gui_memory.json"
)


class GuiMemory:

    def __init__(self):

        os.makedirs(
            "memory",
            exist_ok=True
        )

        if not os.path.exists(
            MEMORY_PATH
        ):

            with open(
                MEMORY_PATH,
                "w",
                encoding="utf-8"
            ) as f:

                json.dump(
                    {},
                    f,
                    indent=4
                )

    def load(self):

        with open(

            MEMORY_PATH,

            "r",

            encoding="utf-8"

        ) as f:

            return json.load(f)

    def save(self, data):

        with open(

            MEMORY_PATH,

            "w",

            encoding="utf-8"

        ) as f:

            json.dump(

                data,

                f,

                indent=4
            )

    def remember_screen(

        self,

        screen_name,

        gui_map
    ):

        data = self.load()

        data[
            screen_name
        ] = gui_map

        self.save(data)

    def get_screen(

        self,

        screen_name
    ):

        data = self.load()

        return data.get(
            screen_name
        )