from app.ui.runtime.gui_mapper import (
    gui_mapper
)


def build_gui_knowledge(
    image_path: str
):

    elements = gui_mapper(
        image_path
    )

    knowledge = {

        "icons": [],

        "buttons": [],

        "toolbars": [],

        "controls": []
    }

    mapping = {

        "icon": "icons",

        "button": "buttons",

        "toolbar": "toolbars",

        "control": "controls"
    }

    for item in elements:

        element_type = item["type"]

        target = mapping.get(
            element_type
        )

        if not target:
            continue

        knowledge[target].append(
            item
        )

    return knowledge