"""
    Abstract strategy for conflict resolution.
"""
from __future__ import annotations


class ConflictResolutionStrategy:
    def is_conflict(self, incoming_version: int, current_version: int) -> bool:
        raise NotImplementedError


class LastWriterWinsByVersion(ConflictResolutionStrategy):
    """Simple integer-based LWW: accept only if incoming_version > current_version."""

    def is_conflict(self, incoming_version: int, current_version: int) -> bool:
        return incoming_version <= current_version


