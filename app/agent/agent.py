from app.decision.decision_engine import (
    DecisionEngine
)

from app.knowledge.construction.workflow_repository import (
    WorkflowRepository
)

from app.construction.workflow_builder import (
    WorkflowBuilder
)

from app.agent.models.agent_report import (
    AgentReport
)


class Agent:

    def run(
        self,
        context
    ) -> AgentReport:

        decision = (
            DecisionEngine()
            .choose_workflow(
                context
            )
        )

        workflow = (
            WorkflowRepository()
            .load(
                decision.workflow
            )
        )

        plan = (
            WorkflowBuilder()
            .build(
                workflow
            )
        )

        report = AgentReport(

            success=not decision.manual_review,

            construction_plan=plan
        )

        if decision.manual_review:

            report.review_positions.append(1)

            report.messages.append(

                "Position requires review."

            )

        else:

            report.completed_positions = 1

            report.messages.append(

                "Position completed."

            )

        return report