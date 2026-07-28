from __future__ import annotations

from core.paths import PATHS


def initialize() -> None:
    """Create all portable runtime folders from the canonical path registry."""

    PATHS.ensure_runtime_directories()
