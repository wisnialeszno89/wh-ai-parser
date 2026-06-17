from app.runtime.agent_report import (
    AgentReport
)


def test_agent_report():

    report = AgentReport()

    report.executed_actions = 5

    assert (

        report.executed_actions

        ==

        5

    )