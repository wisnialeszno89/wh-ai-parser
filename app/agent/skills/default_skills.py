from app.agent.skills.excel_skill import ExcelSkill
from app.agent.skills.skill_registry import SkillRegistry
from app.agent.skills.wh_window_skill import WHWindowSkill
from app.agent.skills.word_skill import WordSkill


def create_default_skill_registry(
) -> SkillRegistry:
    return SkillRegistry(
        skills=(
            WHWindowSkill(),
            ExcelSkill(),
            WordSkill(),
        )
    )
