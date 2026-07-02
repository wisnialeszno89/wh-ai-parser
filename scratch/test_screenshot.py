from app.runtime.screenshot_provider import ScreenshotProvider

print("=" * 50)
print("SCREENSHOT TEST")
print("=" * 50)

provider = ScreenshotProvider()

image = provider.capture()

print("Screenshot captured successfully!")
print(f"Image shape: {image.shape}")