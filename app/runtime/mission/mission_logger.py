class MissionLogger:

    def print(
        self,
        trace: MissionTrace,
    ) -> None:

        print()
        print("=" * 60)
        print("MISSION TRACE")
        print("=" * 60)

        for i, step in enumerate(trace.steps, start=1):

            print(
                f"{i}. "
                f"{step.action.tool.name:<15}"
                f" success={step.result.success}"
                f" confidence={step.result.confidence:.2f}"
            )