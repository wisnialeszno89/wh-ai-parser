from app.agent.environment.environment_observation import (
    EnvironmentObservation,
)

from app.agent.perception.perception_provider import (
    PerceptionProvider,
)

from app.agent.perception.screen_element_fusion import (
    ScreenElementFusion,
)

from app.agent.perception.screen_scene import (
    ScreenScene,
)


class PerceptionEngine:
    """
    Converts environment observations into semantic scenes.

    Perception providers supply ScreenElement objects independently
    of the technology used to detect them.

    Provider outputs are fused conservatively before the scene is
    exposed to the rest of the Universal Agent Core.
    """

    def __init__(
        self,
        providers: tuple[PerceptionProvider, ...] = (),
        element_fusion: ScreenElementFusion | None = None,
    ) -> None:
        self.providers = providers
        self.element_fusion = (
            element_fusion
            if element_fusion is not None
            else ScreenElementFusion()
        )

    @staticmethod
    def _resolve_active_document(elements):
        # UIA tab metadata remains authoritative even if multimodal fusion
        # chooses a visual/OCR representative whose ScreenElement.kind is no
        # longer "tabitem". Do not discard the original control type carried
        # in metadata, but require explicit document scope from UIA.
        document_tabs = tuple(
            element
            for element in elements
            if (
                isinstance(element.metadata, dict)
                and element.metadata.get("uia_tab_scope") == "document"
                and (
                    element.kind.casefold() == "tabitem"
                    or str(
                        element.metadata.get("uia_control_type", "")
                    ).casefold() == "tabitem"
                )
            )
        )

        def tab_caption(element) -> str | None:
            metadata = element.metadata if isinstance(element.metadata, dict) else {}
            for key in ("name", "semantic_name"):
                value = metadata.get(key)
                if isinstance(value, str) and value.strip():
                    return value.strip()
            label = element.label
            return label.strip() if isinstance(label, str) and label.strip() else None

        selected_documents = tuple(
            caption
            for element in document_tabs
            if element.metadata.get("uia_document_tab_selected") is True
            for caption in (tab_caption(element),)
            if caption is not None
        )

        active_document = (
            selected_documents[0]
            if len(selected_documents) == 1
            else None
        )

        return (
            active_document,
            len(document_tabs),
            len(selected_documents),
        )

    def perceive(
        self,
        observation: EnvironmentObservation,
    ) -> ScreenScene:

        elements: list = []

        for provider in self.providers:
            elements.extend(
                provider.perceive(observation)
            )

        raw_elements = tuple(elements)
        fusion_result = self.element_fusion.fuse(
            raw_elements,
        )

        scene_metadata = dict(observation.metadata)
        scene_metadata["provider_count"] = len(self.providers)
        scene_metadata["raw_element_count"] = len(raw_elements)
        scene_metadata["element_count"] = len(
            fusion_result.elements
        )
        scene_metadata["merged_group_count"] = (
            fusion_result.merged_group_count
        )

        active_document, document_tab_count, selected_document_count = (
            self._resolve_active_document(
                fusion_result.elements,
            )
        )
        scene_metadata["active_document"] = active_document
        scene_metadata["document_tab_count"] = document_tab_count
        scene_metadata["selected_document_tab_count"] = (
            selected_document_count
        )
        scene_metadata["active_document_resolution"] = (
            "resolved"
            if selected_document_count == 1
            else (
                "not_observed"
                if document_tab_count == 0
                else "unresolved"
            )
        )

        return ScreenScene(
            observation=observation,
            elements=fusion_result.elements,
            metadata=scene_metadata,
        )
