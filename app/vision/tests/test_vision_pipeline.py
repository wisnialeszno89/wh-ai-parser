from app.runtime.execution.vision.pipeline.vision_pipeline import (
    VisionPipeline,
)


pipeline = VisionPipeline()

toolbar = pipeline.observe()

print()

print("RESULT")

print(toolbar)