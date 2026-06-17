from app.ui.extractors.extract_toolbar import (
    extract_toolbar
)

from app.ui.extractors.extract_tools import (
    extract_tools
)

from app.ui.models.ui_scene_graph import (
    UISceneGraph
)


IMAGE = "samples/wh_screen.png"

graph = UISceneGraph()

toolbars = extract_toolbar(
    IMAGE
)

graph.objects.extend(
    toolbars
)

actions_toolbar = None

for toolbar in toolbars:

    if toolbar.label == "actions":

        actions_toolbar = toolbar

        break

if actions_toolbar:

    tool_objects = extract_tools(

        IMAGE,

        actions_toolbar
    )

    graph.objects.extend(
        tool_objects
    )

print(graph)