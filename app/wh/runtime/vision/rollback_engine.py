from app.wh.runtime.vision.rollback_result import (
    RollbackResult
)


class RollbackEngine:

    def rollback(

        self,

        brain

    ):

        snapshot = (

            brain.gui_state_history.last()

        )

        if snapshot is None:

            return (

                RollbackResult(

                    success=False

                )

            )

        return (

            RollbackResult(

                success=True,

                restored_snapshot=snapshot

            )

        )