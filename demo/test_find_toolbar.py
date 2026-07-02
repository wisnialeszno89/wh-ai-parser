from app.runtime.screenshot_provider import (
    ScreenshotProvider
)

from app.ui.runtime.find_toolbar_band import (
    find_toolbar_band
)

provider = ScreenshotProvider()

image = provider.capture()

toolbars = find_toolbar_band(
    image
)

print()

print("=" * 60)

print("TOOLBARS")

print("=" * 60)

print()

print(toolbars)