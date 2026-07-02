from app.runtime.screenshot_provider import (
    ScreenshotProvider
)

import cv2

from app.ui.runtime.find_toolbar_tools import (
    find_toolbar_tools
)

print("=" * 60)
print("CAPTURING SCREEN...")
print("=" * 60)

provider = ScreenshotProvider()

image = provider.capture()

cv2.imwrite(
    "current_screen.png",
    image
)

print("Screenshot saved.")

print()
print("=" * 60)
print("SEARCHING TOOLS...")
print("=" * 60)

tools = find_toolbar_tools(
    "current_screen.png"
)

print()
print("=" * 60)
print("FOUND TOOLS")
print("=" * 60)

for tool in tools:

    print(tool)