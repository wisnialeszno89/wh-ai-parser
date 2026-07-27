from app.runtime.execution.vision.pipeline.vision_pipeline import VisionPipeline


class RuntimeVision:

    def __init__(self):

        self.pipeline = VisionPipeline()

    def capture(self):

        return self.pipeline.observe()