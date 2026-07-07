from app.runtime.world.perception_engine import (
    PerceptionEngine,
)


def main():

    world = PerceptionEngine().perceive()

    print()

    print("=" * 60)

    print("WORLD STATE")

    print("=" * 60)

    print()

    print(

        f"Objects: {len(world.objects)}"

    )

    for obj in world.objects:

        print(

            f"{obj.name:<30}"

            f"{obj.confidence:.3f}"

        )

    print()

    print(

        f"Toolbar visible: {world.toolbar_visible}"

    )

    print(

        f"Active tool: {world.active_tool}"

    )


if __name__ == "__main__":

    main()