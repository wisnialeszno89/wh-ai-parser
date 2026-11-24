"""Read-only adapter from persisted correction memory to NaviMind decisions.

Learned wording is not a technical guarantee, an installed-catalogue observation
or GUI action authorization. Only active, scoped and audited suggestions are
exposed as LOCAL_RULE facts for an already-verified memory snapshot.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.agent.learning.navimind_correction_rulebook import LearningScope
from app.agent.learning.navimind_versioned_rule_memory import RuleMemoryStore
from app.agent.reasoning.navimind_evidence_decision_engine import KnowledgeFact, SourceKind


@dataclass(frozen=True)
class MemoryConsultation:
    generation: int
    matched_rule_id: str | None
    proposed_value: str | None
    knowledge: tuple[KnowledgeFact, ...]
    applied_to_desktop: bool = False
    production_approved: bool = False


def consult_saved_rules(
    store: RuleMemoryStore, scope: LearningScope, current_value: str,
) -> MemoryConsultation:
    """Read memory afresh; never trust unverified app-specific suggestions."""
    saved = store.load()
    suggestion = saved.book.suggest(scope, current_value)
    if suggestion is None:
        return MemoryConsultation(saved.generation, None, None, ())
    rule_id, text = suggestion
    return MemoryConsultation(
        generation=saved.generation,
        matched_rule_id=rule_id,
        proposed_value=text,
        knowledge=(
            KnowledgeFact(
                key="learned_description:" + rule_id,
                value=text,
                source=SourceKind.LOCAL_RULE,
                reference=f"rulebook:v1:generation:{saved.generation}:rule:{rule_id}",
                applicable_to=f"{scope.application}/{scope.workflow}/{scope.field}",
                verified=True,
            ),
        ),
    )
