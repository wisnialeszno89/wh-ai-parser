from pathlib import Path

from app.agent.intake.task_document import read_task_document
from tools.run_windowhub_goal_v2 import parse_args


def test_browser_downloaded_task_roundtrips_through_existing_windowhub_intake(tmp_path):
    task_file = tmp_path / "navimind-agent-task.txt"
    goal = "Przygotuj ofertę WindowHub na okno 1230x1478 mm, białe/antracyt.\n"
    task_file.write_text(goal, encoding="utf-8")
    assert read_task_document(task_file) == goal.strip()
    args = parse_args(["--mode", "inspect", "--task-file", str(task_file)])
    assert args.mode == "inspect"
    assert args.task_file == task_file
    assert args.execute_live is False


def test_handoff_importer_cannot_execute_without_explicit_separate_runtime():
    importer = (Path(__file__).resolve().parents[1] /
                "tools" / "import_navimind_chat_task.ps1").read_text(encoding="utf-8")
    assert '[ValidateSet("inspect", "think")]' in importer
    assert "AllowModelRequest" in importer
    assert "TASK_EXECUTION=DISABLED" in importer
    assert "--task-file" in importer
    assert '"--mode", $Mode' in importer
    assert "--execute-live" not in importer
