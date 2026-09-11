from app.agent.skills.agent_skill import AgentSkill


class SkillRegistry:
    """
    Registry of specialized skills available to the agent.

    Multiple skills may eventually support different workflows
    within the same capability.
    """

    def __init__(
        self,
        skills: tuple[AgentSkill, ...] = (),
    ) -> None:
        self._skills = {
            skill.capability_name: skill
            for skill in skills
        }

    def register(
        self,
        skill: AgentSkill,
    ) -> None:
        self._skills[
            skill.capability_name
        ] = skill

    def resolve(
        self,
        capability_name: str,
    ) -> AgentSkill | None:
        return self._skills.get(
            capability_name
        )

    def supports(
        self,
        capability_name: str,
    ) -> bool:
        return capability_name in self._skills

    def all(
        self,
    ) -> tuple[AgentSkill, ...]:
        return tuple(
            self._skills.values()
        )
