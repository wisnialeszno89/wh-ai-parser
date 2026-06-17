from app.knowledge.executor.execution_result import (
    ExecutionResult
)


def test_execution_result():

    result = ExecutionResult(

        success=True,

        log=[]

    )

    assert result.success