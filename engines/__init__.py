"""
Audiobook Studio Engine Package

IMPORTANT:
Do NOT import engine implementations here.

Engine implementations (Kokoro, Piper, XTTS, etc.)
are loaded lazily by EngineManager using importlib.

This prevents PyTorch and other heavy dependencies
from being imported during GUI startup.
"""

__all__ = [
    "EngineFactory",
    "EngineManager",
]