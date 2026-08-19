from __future__ import annotations

from app.runtime.execution.vision.runtime_vision import RuntimeVision


def main() -> None:
    print("=" * 80)
    print("WINDOWHUB CONSTRUCTION DETECTOR LIVE")
    print("=" * 80)
    print("DO NOT CLICK.")
    print("Target: detect the actual finished colored window, not the white canvas/editor.")

    vision = RuntimeVision().capture()
    construction = getattr(vision, "construction", None)

    if construction is None:
        print("[CONSTRUCTION] NONE")
        raise RuntimeError("Finished WindowHub construction was not detected")

    print(
        "[CONSTRUCTION] FOUND "
        f"rect=({construction.x},{construction.y},"
        f"{construction.width}x{construction.height}) "
        f"center={construction.center}"
    )
    print("[PROBE] COMPLETE. No click was sent.")


if __name__ == "__main__":
    main()
