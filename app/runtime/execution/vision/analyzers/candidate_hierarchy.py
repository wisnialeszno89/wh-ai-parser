from __future__ import annotations

from dataclasses import dataclass

from app.runtime.execution.vision.models.vision_candidate import VisionCandidate


@dataclass(frozen=True, slots=True)
class CandidateNode:
    """
    A VisionCandidate together with its direct hierarchical children.
    """

    candidate: VisionCandidate
    children: tuple["CandidateNode", ...]

    @property
    def depth(self) -> int:
        return self.candidate.depth

    @property
    def contour_index(self) -> int:
        return self.candidate.contour_index


class CandidateHierarchy:
    """
    Builds a tree from VisionCandidate contour relationships.

    VisionCandidate.parent_contour_index refers to the original
    OpenCV contour index, so the hierarchy remains valid even when
    candidates are filtered or reordered.
    """

    def build(
        self,
        candidates: list[VisionCandidate],
    ) -> tuple[CandidateNode, ...]:
        if not candidates:
            return ()

        by_contour_index = {
            candidate.contour_index: candidate
            for candidate in candidates
        }

        children_by_parent: dict[int, list[VisionCandidate]] = {}

        roots: list[VisionCandidate] = []

        for candidate in candidates:
            parent_index = candidate.parent_contour_index

            if (
                parent_index is None
                or parent_index not in by_contour_index
            ):
                roots.append(candidate)
                continue

            children_by_parent.setdefault(parent_index, []).append(candidate)

        def build_node(candidate: VisionCandidate) -> CandidateNode:
            children = tuple(
                build_node(child)
                for child in children_by_parent.get(
                    candidate.contour_index,
                    [],
                )
            )

            return CandidateNode(
                candidate=candidate,
                children=children,
            )

        return tuple(build_node(root) for root in roots)
