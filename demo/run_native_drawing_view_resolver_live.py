from app.runtime.execution.native_drawing_view_resolver import NativeDrawingViewResolver
from app.runtime.execution.native_toolbar_resolver import NativeToolbarResolver


def main() -> None:
    print("=" * 80)
    print("WINDOWHUB NATIVE DRAWING VIEW RESOLVER LIVE")
    print("=" * 80)
    print("SAFE MODE: NO CLICKS")

    root, toolbar = NativeToolbarResolver()._find_root_and_toolbar()
    print(f"[NATIVE] root={root} toolbar={toolbar}")

    result = NativeDrawingViewResolver().resolve(
        root_hwnd=root,
        toolbar_hwnd=toolbar,
    )

    print("\n[RESULT]")
    print(f"[DRAWING VIEW] hwnd={result['hwnd']}")
    print(f"[DRAWING VIEW] class={result['class']!r}")
    print(f"[DRAWING VIEW] title={result['title']!r}")
    print(f"[DRAWING VIEW] rect={result['rect']}")
    print(f"[DRAWING VIEW] hits={result['hits']}")
    print("[PROBE] COMPLETE. No clicks were sent.")


if __name__ == "__main__":
    main()
