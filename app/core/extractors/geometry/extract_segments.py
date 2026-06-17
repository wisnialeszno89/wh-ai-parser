from app.core.scene.models.scene_object import (
    SceneObject
)


MIN_SEGMENT_WIDTH = 40


def extract_segments(

    frame,

    mullions
):

    segments = []

    frame_left = frame.x

    frame_right = (
        frame.x + frame.width
    )

    frame_top = frame.y

    frame_height = frame.height

    if not mullions:

        segments.append(

            SceneObject(

                id="segment_0",

                object_type="segment",

                x=frame_left,

                y=frame_top,

                width=frame.width,

                height=frame_height,

                label="UNKNOWN"
            )
        )

        return segments

    mullions = sorted(
        mullions,
        key=lambda m: m.x
    )

    filtered = []

    for mullion in mullions:

        distance_from_left = (
            mullion.x - frame_left
        )

        distance_from_right = (
            frame_right - mullion.x
        )

        if (
            distance_from_left < MIN_SEGMENT_WIDTH
            or
            distance_from_right < MIN_SEGMENT_WIDTH
        ):

            continue

        filtered.append(
            mullion
        )

    mullions = filtered

    current_left = frame_left

    for index, mullion in enumerate(mullions):

        segment_width = (
            mullion.x - current_left
        )

        if segment_width < MIN_SEGMENT_WIDTH:

            continue

        segments.append(

            SceneObject(

                id=f"segment_{index}",

                object_type="segment",

                x=current_left,

                y=frame_top,

                width=segment_width,

                height=frame_height,

                label="UNKNOWN"
            )
        )

        current_left = (
            mullion.x + mullion.width
        )

    last_width = (
        frame_right - current_left
    )

    if last_width >= MIN_SEGMENT_WIDTH:

        segments.append(

            SceneObject(

                id="segment_last",

                object_type="segment",

                x=current_left,

                y=frame_top,

                width=last_width,

                height=frame_height,

                label="UNKNOWN"
            )
        )

    return segments