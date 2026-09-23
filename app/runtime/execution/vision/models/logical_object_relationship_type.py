from enum import Enum


class LogicalObjectRelationshipType(str, Enum):
    """
    Spatial or structural relationship between two logical visual objects.

    Relationships are intentionally independent from semantic GUI meaning.
    """

    CONTAINS = "contains"
    OVERLAPS = "overlaps"
    ADJACENT = "adjacent"
    ALIGNED_HORIZONTAL = "aligned_horizontal"
    ALIGNED_VERTICAL = "aligned_vertical"
    SAME_GROUP = "same_group"
