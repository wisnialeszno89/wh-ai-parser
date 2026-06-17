import cv2

from app.core.scene.models.scene_graph import (
    SceneGraph
)


COLORS = {

    "frame": (0, 255, 0),

    "mullion": (0, 0, 255),

    "segment": (255, 0, 0),

    "dimension": (0, 255, 255)
}


def render_scene_graph(

    image_path: str,

    graph: SceneGraph,

    output_path: str
):

    image = cv2.imread(
        image_path
    )

    for obj in graph.objects:

        color = COLORS.get(

            obj.object_type,

            (255, 255, 255)
        )

        cv2.rectangle(

            image,

            (obj.x, obj.y),

            (
                obj.x + obj.width,

                obj.y + obj.height
            ),

            color,

            2
        )

        label = (
            f"{obj.object_type}"
        )

        if obj.label:

            label += (
                f": {obj.label}"
            )

        cv2.putText(

            image,

            label,

            (obj.x, obj.y - 10),

            cv2.FONT_HERSHEY_SIMPLEX,

            0.5,

            color,

            1
        )

    cv2.imwrite(
        output_path,
        image
    )

    print(
        f"[DEBUG] saved: "
        f"{output_path}"
    )