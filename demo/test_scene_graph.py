from app.wh.vision.mss_screenshot_engine import (
    MSSScreenshotEngine,
)

from app.wh.vision.screen_scene_graph import (
    ScreenSceneGraph,
)


def main():

    print("=" * 60)
    print("SCENE GRAPH TEST")
    print("=" * 60)

    engine = MSSScreenshotEngine()

    screenshot = engine.capture()

    print(
        f"Screenshot: {screenshot.width}x{screenshot.height}"
    )

    scene = ScreenSceneGraph()

    objects = scene.analyze(
        screenshot=screenshot,
        templates_dir="templates",
    )

    print()
    print("=" * 60)
    print("FOUND OBJECTS")
    print("=" * 60)

    for obj in objects:

        print(
            f"{obj.name:<30}"
            f"conf={obj.confidence:.3f}   "
            f"x={obj.x:<5} "
            f"y={obj.y:<5}"
        )

    print()
    print(f"TOTAL OBJECTS: {len(objects)}")


if __name__ == "__main__":
    main()