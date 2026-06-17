from app.core.extractors.scene.build_scene_graph import (
    build_scene_graph
)

from app.core.debug.render_scene_graph import (
    render_scene_graph
)


IMAGE = "samples/fix_ru_window.png"

graph = build_scene_graph(
    IMAGE
)

print(graph)

render_scene_graph(

    IMAGE,

    graph,

    "outputs/debug/scene_graph_debug.jpg"
)
print("\nRELATIONS:\n")

for relation in graph.relations:

    print(relation)