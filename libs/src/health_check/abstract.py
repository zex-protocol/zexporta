from abc import ABC, abstractmethod


class Checkable(ABC):
    @abstractmethod
    def __init__(self):
        """Initialize the Checkable component"""

    @abstractmethod
    async def is_healthy() -> bool:
        """Check the component is healthy or not"""
