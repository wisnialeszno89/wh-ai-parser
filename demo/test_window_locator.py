from app.runtime.execution.window.window_locator import (
    WindowLocator,
)


def main():

    print()
    print("=" * 60)
    print("WINDOW LOCATOR TEST")
    print("=" * 60)

    locator = WindowLocator()

    rect = locator.locate()

    print()
    print("SUCCESS")
    print(rect)


if __name__ == "__main__":

    main()