from app.wh.runtime.vision.autonomous_recovery_result import (
    AutonomousRecoveryResult
)


class AutonomousRecoveryManager:

    def recover(

        self,

        reason,

        brain

    ):

        rollback_result = (

            brain.rollback_engine.rollback(

                brain

            )

        )

        plan = (

            brain.recovery_planner.create(

                reason,

                brain

            )

        )

        recovery_result = (

            brain.recovery_executor.execute(

                plan

            )

        )

        return (

            AutonomousRecoveryResult(

                rollback_result=rollback_result,

                recovery_result=recovery_result,

                success=(

                    rollback_result.success

                    and

                    recovery_result.success

                )

            )

        )