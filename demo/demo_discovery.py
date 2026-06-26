import cv2

from app.discovery.discovery_pipeline import (
    DiscoveryPipeline
)


def main():

    image = cv2.imread(
        "test_data/wh_screen.png"
    )

    if image is None:

        raise FileNotFoundError(

            "Cannot load test_data/wh_screen.png"

        )

    pipeline = DiscoveryPipeline()

    result = pipeline.run(

        image

    )

    print(result)


if __name__ == "__main__":

    main()