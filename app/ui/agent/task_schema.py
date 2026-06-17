from dataclasses import dataclass


@dataclass
class Task:

    task: str

    params: dict