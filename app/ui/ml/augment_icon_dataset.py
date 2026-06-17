import os
import cv2
import random
import numpy as np


SOURCE_DIRS = [

    "dataset/icon",

    "dataset_archive"
]


OUTPUT_DIR = (
    "dataset_augmented"
)


AUGMENTATIONS_PER_IMAGE = 25


def augment_image(image):

    result = image.copy()

    angle = random.uniform(-12, 12)

    h, w = result.shape[:2]

    matrix = cv2.getRotationMatrix2D(

        (w // 2, h // 2),

        angle,

        1.0
    )

    result = cv2.warpAffine(

        result,

        matrix,

        (w, h),

        borderMode=cv2.BORDER_REPLICATE
    )

    brightness = random.uniform(

        0.8,

        1.2
    )

    result = np.clip(

        result * brightness,

        0,

        255
    ).astype(np.uint8)

    if random.random() > 0.5:

        result = cv2.GaussianBlur(

            result,

            (3, 3),

            0
        )

    noise = np.random.normal(

        0,

        5,

        result.shape
    )

    result = np.clip(

        result + noise,

        0,

        255
    ).astype(np.uint8)

    return result


def collect_images():

    images = []

    for source_dir in SOURCE_DIRS:

        for root, _, files in os.walk(
            source_dir
        ):

            for file in files:

                if not file.endswith(
                    ".png"
                ):
                    continue

                images.append(

                    os.path.join(
                        root,
                        file
                    )
                )

    return images


def main():

    os.makedirs(

        OUTPUT_DIR,

        exist_ok=True
    )

    images = collect_images()

    print(
        f"[FOUND] {len(images)} images"
    )

    saved = 0

    for image_path in images:

        image = cv2.imread(
            image_path
        )

        class_name = os.path.basename(

            os.path.dirname(
                image_path
            )
        )

        class_dir = os.path.join(

            OUTPUT_DIR,

            class_name
        )

        os.makedirs(

            class_dir,

            exist_ok=True
        )

        for i in range(

            AUGMENTATIONS_PER_IMAGE
        ):

            augmented = augment_image(
                image
            )

            output_path = os.path.join(

                class_dir,

                f"{saved}.png"
            )

            cv2.imwrite(

                output_path,

                augmented
            )

            saved += 1

    print(
        f"[GENERATED] {saved}"
    )


if __name__ == "__main__":

    main()