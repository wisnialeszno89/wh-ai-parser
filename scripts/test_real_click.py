from app.wh.runtime.agent_workflow import (
    AgentWorkflow
)

print()

print(
    "START"
)

workflow = AgentWorkflow()

result = workflow.add_position()

print()

print(
    "CONFIDENCE:",
    result.confidence
)

print()

print(
    "DONE"
)