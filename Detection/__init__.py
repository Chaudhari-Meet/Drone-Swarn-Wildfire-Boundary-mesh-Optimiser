"""Object detection modules for animals and persons."""

from .Detection import (
    Detection, DetectionType, DetectionCategory,
    AnimalDetector, PersonDetector
)

__all__ = [
    "Detection",
    "DetectionType",
    "DetectionCategory",
    "AnimalDetector",
    "PersonDetector"
]
