import pyautogui
import time


time.sleep(3)

print(
    "\nSZUKAM IKONY...\n"
)

pos = pyautogui.locateCenterOnScreen(
    "automation/templates/frame_tool.png",
    confidence=0.8
)

print(
    "FOUND:",
    pos
)