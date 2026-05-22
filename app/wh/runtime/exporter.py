import json

from pathlib import Path


class RuntimeExporter:

    @staticmethod
    def export_actions(

        session,
        history
    ):

        path = (
            session.folder.root /
            "actions.json"
        )

        data = {

            "actions": history.items
        }

        with open(

            path,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(

                data,

                f,

                indent=2
            )

        print(
            f"[EXPORT] "
            f"actions -> {path}"
        )