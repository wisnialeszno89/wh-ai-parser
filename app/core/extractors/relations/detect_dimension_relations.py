from app.core.scene.models.scene_relation import (
    SceneRelation
)


def detect_dimension_relations(graph):

    relations = []

    dimensions = [

        obj

        for obj in graph.objects

        if obj.object_type == "dimension"
    ]

    segments = [

        obj

        for obj in graph.objects

        if obj.object_type == "segment"
    ]

    for dim in dimensions:

        if dim.orientation == "horizontal":

            continue

        nearest_segment = None

        nearest_distance = 999999

        for segment in segments:

            dx = (
                segment.x - dim.x
            )

            dy = (
                segment.y - dim.y
            )

            distance = (
                dx * dx + dy * dy
            ) ** 0.5

            if distance < nearest_distance:

                nearest_distance = distance

                nearest_segment = segment

        if nearest_segment:

            if dim.orientation == "horizontal":

                relation_type = (
                    "controls_width"
                )

            else:

                relation_type = (
                    "controls_height"
                )

            relations.append(

                SceneRelation(

                    source_id=dim.id,

                    target_id=nearest_segment.id,

                    relation_type=relation_type
                )
            )

    return relations