"""Temporal smoothing and depth-to-grayscale conversion."""

from __future__ import annotations

from typing import Optional

import numpy as np


def depth_to_grayscale(depth: np.ndarray, invert: bool = False) -> np.ndarray:
    """Normalize a float32 depth map to 0–255 uint8 grayscale."""
    d_min = depth.min()
    d_max = depth.max()
    if d_max - d_min < 1e-6:
        normalized = np.zeros_like(depth, dtype=np.uint8)
    else:
        normalized = ((depth - d_min) / (d_max - d_min) * 255).astype(np.uint8)

    if invert:
        normalized = 255 - normalized
    return normalized


class TemporalSmoother:
    """Exponential moving average across consecutive depth frames."""

    def __init__(self, alpha: float):
        self.alpha = alpha          # 1.0 = no smoothing, 0.05 = heavy
        self.previous: Optional[np.ndarray] = None

    def smooth(self, current: np.ndarray) -> np.ndarray:
        if self.previous is None:
            self.previous = current.copy()
            return current
        blended = self.alpha * current + (1.0 - self.alpha) * self.previous
        self.previous = blended.copy()
        return blended

    def reset(self) -> None:
        self.previous = None
