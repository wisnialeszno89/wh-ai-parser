from app.agent.runtime.task_quality_metrics import TaskQualityMetrics


def test_quality_metrics_defaults_are_stable():
    metrics = TaskQualityMetrics()
    assert metrics.quality_state == "incomplete"
    assert metrics.verification_success_rate == 0.0
