from app.core.scene.models.scene_graph import (
    SceneGraph
)

from app.core.extractors.geometry.extract_frames import (
    extract_frames
)

from app.core.extractors.geometry.extract_mullions import (
    extract_mullions
)

from app.core.extractors.geometry.extract_segments import (
    extract_segments
)

from app.core.extractors.dimensions.extract_dimensions import (
    extract_dimensions
)

from app.core.extractors.relations.detect_dimension_relations import (
    detect_dimension_relations
)


def build_scene_graph(image_path: str):

    graph = SceneGraph()

    frames = extract_frames(
        image_path
    )

    if not frames:

        return graph

    frame = frames[0]

    mullions = extract_mullions(

        image_path,

        frame
    )

    segments = extract_segments(

        frame,

        mullions
    )

    dimensions = extract_dimensions(

    image_path,

    frame
    )

    graph.objects.extend(
        frames
    )

    graph.objects.extend(
        mullions
    )

    graph.objects.extend(
        segments
    )

    graph.objects.extend(
        dimensions
    )

    graph.relations.extend(

        detect_dimension_relations(
            graph
        )
    )

    return graph