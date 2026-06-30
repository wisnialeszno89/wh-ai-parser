from dataclasses import dataclass, field

from app.brain.memory.case_memory import (
    CaseMemory
)

from app.brain.memory.product_memory import (
    ProductMemory
)

from app.brain.memory.vocabulary_memory import (
    VocabularyMemory
)

from app.brain.memory.construction_memory import (
    ConstructionMemory
)


@dataclass
class Brain:

    vocabulary: VocabularyMemory = field(
        default_factory=VocabularyMemory
    )

    products: ProductMemory = field(
        default_factory=ProductMemory
    )

    constructions: ConstructionMemory = field(
        default_factory=ConstructionMemory
    )

    cases: CaseMemory = field(
        default_factory=CaseMemory
    )