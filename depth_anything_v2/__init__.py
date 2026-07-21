"""
Depth Anything V2 — vendored model architecture from the official repository.
https://github.com/DepthAnything/Depth-Anything-V2

This package contains ONLY the model definition code.
Checkpoint files (.pth) are stored in the sibling ``models/`` directory.
"""

from .dpt import DepthAnythingV2

__all__ = ["DepthAnythingV2"]
