class RuntimeAssertions:

    @staticmethod
    def assert_tool(

        runtime,
        tool
    ):

        if tool is None:

            raise RuntimeError(
                "No active tool"
            )

        print(
            f"[ASSERT] "
            f"tool OK "
            f"({tool.value})"
        )

        runtime.session.vision.assert_tool_active(
            tool.value
        )