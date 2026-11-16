"""Safe planning of unresolved agent tasks and bounded salesperson handoffs.

The agent may skip optional independent steps; it MUST pause when unresolved
work invalidates later work. Designed for reuse beyond WindowHub.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from collections.abc import Callable
import time


class TaskState(str, Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    SKIPPED = "skipped"
    BLOCKED = "blocked"


@dataclass(frozen=True)
class TaskItem:
    key: str
    required: bool = True
    depends_on: tuple[str, ...] = ()


@dataclass(frozen=True)
class UnresolvedIssue:
    task: str
    reason: str
    outcome: str


@dataclass
class TaskLedger:
    tasks: dict[str, TaskItem]
    status: dict[str, TaskState] = field(default_factory=dict)
    issues: list[UnresolvedIssue] = field(default_factory=list)

    def __post_init__(self):
        if not self.tasks:
            raise ValueError("empty_task_graph")
        if any(k != t.key for k, t in self.tasks.items()):
            raise ValueError("task_key_mismatch")
        if any(d not in self.tasks or d == k for k, item in self.tasks.items() for d in item.depends_on):
            raise ValueError("invalid_task_dependencies")
        # Validate against indirect circular dependencies.
        visited, in_path = set(), set()
        def visit(key):
            if key in in_path:
                raise ValueError("cyclic_task_dependencies")
            if key in visited:
                return
            in_path.add(key)
            for dep in self.tasks[key].depends_on:
                visit(dep)
            in_path.remove(key)
            visited.add(key)
        for key in self.tasks:
            visit(key)

    def state(self, key: str) -> TaskState:
        return self.status.get(key, TaskState.PENDING)

    def ready(self) -> tuple[str, ...]:
        return tuple(
            key for key, task in self.tasks.items()
            if self.state(key) is TaskState.PENDING
            and all(self.state(dep) is TaskState.VERIFIED for dep in task.depends_on)
        )

    def verify(self, key: str) -> None:
        if key not in self.ready():
            raise ValueError("task_dependencies_not_verified")
        self.status[key] = TaskState.VERIFIED

    def unresolved(self, key: str, *, reason: str) -> str:
        if key not in self.tasks or self.state(key) is not TaskState.PENDING:
            raise ValueError("task_not_pending")
        if not isinstance(reason, str) or not reason.strip():
            raise ValueError("issue_reason_required")
        task = self.tasks[key]
        # A required item cannot be silently omitted. Optional items may be
        # omitted, but their dependants will be blocked unless independently
        # proved valid.
        state = TaskState.BLOCKED if task.required else TaskState.SKIPPED
        self.status[key] = state
        self.issues.append(UnresolvedIssue(key, reason.strip()[:240], state.value))
        for other in self.tasks:
            if other == key or self.state(other) is not TaskState.PENDING:
                continue
            if self._requires(other, key):
                self.status[other] = TaskState.BLOCKED
                self.issues.append(UnresolvedIssue(
                    other, "depends_on_unresolved:" + key, "blocked"
                ))
        return state.value

    def _requires(self, key: str, prerequisite: str) -> bool:
        return prerequisite in self.tasks[key].depends_on or any(
            self._requires(dep, prerequisite) for dep in self.tasks[key].depends_on
        )

    def final_status(self) -> str:
        if any(self.state(k) is TaskState.BLOCKED for k in self.tasks):
            return "blocked_partial"
        if any(self.state(k) is TaskState.SKIPPED for k in self.tasks):
            return "partial_requires_review"
        if all(self.state(k) is TaskState.VERIFIED for k in self.tasks):
            return "ready_for_salesperson_review"
        return "in_progress"


def append_unresolved_issues(ledger: TaskLedger, *, path=None) -> int:
    """Persist minimal local evidence of skipped/blocked tasks.

    No customer details, raw screen content, control values or user prompts.
    Call after a task transition; not automatically on every observation.
    """
    from pathlib import Path
    import json
    file = Path(path) if path is not None else (
        Path.home() / ".windowhub_agent" / "unresolved_tasks.jsonl"
    )
    file.parent.mkdir(parents=True, exist_ok=True)
    rows = [
        {
            "schema": 1,
            "task": issue.task,
            "reason": issue.reason,
            "outcome": issue.outcome,
        }
        for issue in ledger.issues
    ]
    if not rows:
        return 0
    # Caller retains the ledger's single responsibility for deduplication.
    with file.open("a", encoding="utf-8") as stream:
        for row in rows:
            stream.write(json.dumps(row, ensure_ascii=False) + "\\n")
    return len(rows)


def timed_salesperson_prompt(question: str, *, timeout_seconds: float = 60.0,
                             reader: Callable | None = None) -> str | None:
    """Console prompt that returns None after bounded wait.

    On Windows we poll msvcrt instead of blocking on input(), so the stated
    timeout really works. Tests can supply a reader with (question, timeout).
    """
    if not isinstance(question, str) or not question.strip():
        raise ValueError("empty_question")
    if not 1 <= timeout_seconds <= 300:
        raise ValueError("invalid_handoff_timeout")
    if reader is not None:
        return reader(question, timeout_seconds)
    import os
    if os.name != "nt":
        raise RuntimeError("interactive_timeout_requires_windows")
    import msvcrt
    print(question + f" [limit {int(timeout_seconds)} s]: ", end="", flush=True)
    deadline = time.monotonic() + timeout_seconds
    keys = []
    while time.monotonic() < deadline:
        if not msvcrt.kbhit():
            time.sleep(0.05)
            continue
        char = msvcrt.getwch()
        if char in ("\r", "\n"):
            print()
            return "".join(keys)
        if char == "\x03":
            raise KeyboardInterrupt
        if char in ("\b", "\x7f"):
            if keys:
                keys.pop()
            continue
        # Ignore navigation/special keys and prevent arbitrary long payload.
        if char in ("\x00", "\xe0"):
            msvcrt.getwch()
            continue
        if char.isprintable() and len(keys) < 160:
            keys.append(char)
    print("\nHANDOFF_TIMEOUT=True")
    return None
