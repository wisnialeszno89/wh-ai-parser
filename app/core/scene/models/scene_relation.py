from dataclasses import dataclass


@dataclass
class SceneRelation:

    source_id: str

    target_id: str

    relation_type: str