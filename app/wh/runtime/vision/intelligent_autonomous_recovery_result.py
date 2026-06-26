from dataclasses import (
    dataclass
)

from app.wh.runtime.vision.rollback_result import (
    RollbackResult
)

from app.wh.runtime.vision.recovery_execution_result import (
    RecoveryExecutionResult
)


@dataclass
class IntelligentAutonomousRecoveryResult:

    rollback_result: RollbackResult

    recovery_result: RecoveryExecutionResult

    success: bool