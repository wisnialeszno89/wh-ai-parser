import cv2

from app.core.scene.models.scene_object import (
    SceneObject
)


def extract_frames(image_path: str):

    image = cv2.imread(
        image_path
    )

    gray = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2GRAY
    )

    edges = cv2.Canny(
        gray,
        50,
        150
    )

    contours, _ = cv2.findContours(

        edges,

        cv2.RETR_EXTERNAL,

        cv2.CHAIN_APPROX_SIMPLE
    )

    if not contours:

        return []

    largest = max(
        contours,
        key=cv2.contourArea
    )

    x, y, w, h = cv2.boundingRect(
        largest
    )

    return [

        SceneObject(

            id="frame_1",

            object_type="frame",

            x=x,
            y=y,

            width=w,
            height=h
        )
    ]