from __future__ import annotations

from collections.abc import Iterable
from typing import Mapping

from app.agent.memory.agent_memory import (
    AgentExperience,
    AgentMemoryRepository,
)


class AgentMemoryStore:
    """
    In-memory cache with optional durable persistence for experiences.
    """

    def __init__(
        self,
        *,
        experiences: Iterable[AgentExperience] = (),
        repository: AgentMemoryRepository | None = None,
        load_persisted: bool = True,
    ) -> None:
        self.repository = repository
        self._experiences = {
            experience.experience_id: experience
            for experience in experiences
        }

        if load_persisted and self.repository is not None:
            self.load_persisted()

    def add(self, experience: AgentExperience) -> AgentExperience:
        self._experiences[experience.experience_id] = experience

        if self.repository is not None:
            self.repository.save(experience)

        return experience

    def get(self, experience_id: str) -> AgentExperience | None:
        experience = self._experiences.get(experience_id)
        if experience is not None:
            return experience

        if self.repository is None:
            return None

        experience = self.repository.get(experience_id)
        if experience is not None:
            self._experiences[experience.experience_id] = experience

        return experience

    def all(self) -> tuple[AgentExperience, ...]:
        return tuple(
            sorted(
                self._experiences.values(),
                key=lambda item: (
                    item.experience_id,
                    item.kind,
                ),
            )
        )

    def recent(
        self,
        *,
        limit: int = 10,
        application: str | None = None,
        kind: str | None = None,
    ) -> tuple[AgentExperience, ...]:
        if limit < 1:
            raise ValueError("limit must be positive.")

        experiences = list(self._experiences.values())

        if application is not None:
            application_key = application.strip().casefold()
            experiences = [
                experience
                for experience in experiences
                if (
                    isinstance(experience.application, str)
                    and experience.application.strip().casefold()
                    == application_key
                )
            ]

        if kind is not None:
            kind_key = kind.strip().casefold()
            experiences = [
                experience
                for experience in experiences
                if experience.kind.strip().casefold() == kind_key
            ]

        experiences.sort(
            key=lambda item: item.experience_id,
            reverse=True,
        )
        return tuple(experiences[:limit])

    def load_persisted(self) -> int:
        if self.repository is None:
            return 0

        loaded = self.repository.all()
        for experience in loaded:
            self._experiences[experience.experience_id] = experience

        return len(loaded)

    @staticmethod
    def build_experience(
        *,
        experience_id: str,
        kind: str,
        application: str | None,
        intent: str | None,
        workflow_id: str | None,
        outcome: str,
        summary: str,
        metadata: Mapping[str, object] | None = None,
    ) -> AgentExperience:
        return AgentExperience(
            experience_id=experience_id,
            kind=kind,
            application=application,
            intent=intent,
            workflow_id=workflow_id,
            outcome=outcome,
            summary=summary,
            metadata=dict(metadata or {}),
        )
