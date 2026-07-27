import time

from app.runtime.execution.keyboard.keyboard_controller import (
    KeyboardController,
)


def main():

    keyboard = KeyboardController()

    print()

    print("Typing in 5 seconds...")

    time.sleep(5)

    keyboard.write("HELLO WINDOW HUB")

    keyboard.press("enter")

    keyboard.write("123456")

    keyboard.press("enter")


if __name__ == "__main__":

    main()