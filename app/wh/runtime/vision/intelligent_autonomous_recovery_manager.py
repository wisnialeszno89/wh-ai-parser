from app.wh.runtime.vision.intelligent_autonomous_recovery_result import (
    IntelligentAutonomousRecoveryResult
)


class IntelligentAutonomousRecoveryManager:

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

            brain.intelligent_recovery_planner.create(

                reason,

                brain

            )

        )

        recovery_result = (

            brain.recovery_executor.execute(

                plan

            )

        )

        if recovery_result.success:

            brain.recovery_learning_engine.learn(

                reason,

                recovery_result.strategy,

                brain

            )

        return (

            IntelligentAutonomousRecoveryResult(

                rollback_result=rollback_result,

                recovery_result=recovery_result,

                success=(

                    rollback_result.success

                    and

                    recovery_result.success

                )

            )

        )