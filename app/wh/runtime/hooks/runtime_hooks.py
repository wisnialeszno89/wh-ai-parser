class RuntimeHooks:

    def before_click(

        self,
        target
    ):

        print(
            f"[HOOK] "
            f"before_click "
            f"{target}"
        )

    def after_click(

        self,
        target
    ):

        print(
            f"[HOOK] "
            f"after_click "
            f"{target}"
        )