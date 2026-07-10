from app.runtime.execution.vision.pipeline.vision_pipeline import VisionPipeline


pipeline = VisionPipeline()

context = pipeline.observe()

print()

print("====== RESULT ======")
print(context.window)
print(context.screenshot.width, context.screenshot.height)
print(context.toolbar)

print()

print("====== SECTIONS ======")

for section in context.toolbar.children:
    print(section.id, section.bounds)