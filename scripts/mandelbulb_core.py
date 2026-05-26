#!/usr/bin/env python3
"""
Shared mathematical primitives used by both visualization scripts.

Covers: Mandelbulb escape test, surface boundary search, sphere sampling,
arithmetic signal utilities, and path densification helpers.
"""

from __future__ import annotations

import math
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np

if "MPLCONFIGDIR" not in os.environ:
    mpl_dir = Path(tempfile.gettempdir()) / "mandelbulb_mplconfig"
    mpl_dir.mkdir(parents=True, exist_ok=True)
    os.environ["MPLCONFIGDIR"] = str(mpl_dir)

if not os.environ.get("DISPLAY") and os.name != "nt":
    import matplotlib

    matplotlib.use("Agg")

import matplotlib.pyplot as plt

if TYPE_CHECKING:
    pass


@dataclass(frozen=True)
class MandelbulbConfig:
    power: int = 8
    max_iter: int = 18
    bailout: float = 4.0
    search_radius: float = 1.9
    radial_steps: int = 48
    refine_steps: int = 7


def mandelbulb_escape(c: np.ndarray, cfg: MandelbulbConfig) -> tuple[bool, int, float]:
    """Return whether ``c`` escaped, the escape iteration, and final radius."""
    z = np.zeros(3, dtype=float)
    for iteration in range(cfg.max_iter):
        x, y, zc = z
        radius = math.sqrt(x * x + y * y + zc * zc)
        if radius > cfg.bailout:
            return True, iteration, radius
        if radius == 0.0:
            theta = 0.0
            phi = 0.0
        else:
            theta = math.atan2(y, x)
            phi = math.acos(max(-1.0, min(1.0, zc / radius)))
        rn = radius**cfg.power
        theta_n = theta * cfg.power
        phi_n = phi * cfg.power
        sin_phi = math.sin(phi_n)
        z = np.array(
            [
                rn * sin_phi * math.cos(theta_n),
                rn * sin_phi * math.sin(theta_n),
                rn * math.cos(phi_n),
            ],
            dtype=float,
        )
        z += c
    final_radius = float(np.linalg.norm(z))
    return False, cfg.max_iter, final_radius


def approximate_mandelbulb_surface_radius(
    direction: np.ndarray, cfg: MandelbulbConfig
) -> tuple[float, int]:
    """
    Approximate the Mandelbulb boundary radius along one unit direction.

    The Mandelbulb is treated as star-shaped around the origin for this
    visualization, which is sufficient for path projection.
    """
    direction = direction / np.linalg.norm(direction)
    probe_radii = np.linspace(0.0, cfg.search_radius, cfg.radial_steps)
    prev_radius = 0.0
    prev_inside = True
    prev_escape_iter = cfg.max_iter

    for radius in probe_radii[1:]:
        escaped, escape_iter, _ = mandelbulb_escape(direction * radius, cfg)
        inside = not escaped
        if prev_inside and not inside:
            lo = prev_radius
            hi = float(radius)
            best_escape = escape_iter
            for _ in range(cfg.refine_steps):
                mid = 0.5 * (lo + hi)
                escaped_mid, escape_iter_mid, _ = mandelbulb_escape(direction * mid, cfg)
                if escaped_mid:
                    hi = mid
                    best_escape = escape_iter_mid
                else:
                    lo = mid
                    prev_escape_iter = escape_iter_mid
            return lo, max(prev_escape_iter, best_escape)
        prev_inside = inside
        prev_radius = float(radius)
        prev_escape_iter = escape_iter

    return prev_radius, prev_escape_iter


def fibonacci_sphere(samples: int) -> np.ndarray:
    """Evenly distributed directions on the unit sphere via golden-angle ordering."""
    points = np.zeros((samples, 3), dtype=float)
    golden_angle = math.pi * (3.0 - math.sqrt(5.0))
    for i in range(samples):
        y = 1.0 - (2.0 * i) / max(1, samples - 1)
        radius = math.sqrt(max(0.0, 1.0 - y * y))
        theta = golden_angle * i
        points[i] = (
            math.cos(theta) * radius,
            y,
            math.sin(theta) * radius,
        )
    return points


def normalise(values: np.ndarray) -> np.ndarray:
    values = np.asarray(values, dtype=float)
    span = float(values.max() - values.min())
    if span == 0.0:
        return np.zeros_like(values)
    return (values - values.min()) / span


def odd_primes(count: int) -> list[int]:
    primes: list[int] = []
    candidate = 3
    while len(primes) < count:
        is_prime = True
        limit = int(math.sqrt(candidate)) + 1
        for divisor in range(3, limit, 2):
            if candidate % divisor == 0:
                is_prime = False
                break
        if is_prime:
            primes.append(candidate)
        candidate += 2
    return primes


def densify_angles(
    theta: np.ndarray, phi: np.ndarray, hover: np.ndarray, factor: int = 4
) -> tuple[np.ndarray, np.ndarray]:
    """Linearly densify an angular path so projected curves render smoothly."""
    base_t = np.linspace(0.0, 1.0, len(theta))
    dense_count = max(len(theta), (len(theta) - 1) * factor + 1)
    dense_t = np.linspace(0.0, 1.0, dense_count)
    theta_dense = np.interp(dense_t, base_t, np.unwrap(theta))
    phi_dense = np.interp(dense_t, base_t, phi)
    hover_dense = np.interp(dense_t, base_t, hover)
    directions = np.column_stack(
        (
            np.cos(theta_dense) * np.sin(phi_dense),
            np.sin(theta_dense) * np.sin(phi_dense),
            np.cos(phi_dense),
        )
    )
    return directions, hover_dense


def densify_directions(
    directions: np.ndarray, hover: np.ndarray, factor: int = 4
) -> tuple[np.ndarray, np.ndarray]:
    """Linearly densify a Cartesian direction path and re-normalise to the unit sphere."""
    base_t = np.linspace(0.0, 1.0, len(directions))
    dense_count = max(len(directions), (len(directions) - 1) * factor + 1)
    dense_t = np.linspace(0.0, 1.0, dense_count)
    dense = np.zeros((dense_count, 3), dtype=float)
    for axis in range(3):
        dense[:, axis] = np.interp(dense_t, base_t, directions[:, axis])
    dense /= np.linalg.norm(dense, axis=1, keepdims=True)
    hover_dense = np.interp(dense_t, base_t, hover)
    return dense, hover_dense


def set_equal_axes(ax: plt.Axes, points: np.ndarray) -> None:
    """Force equal axis scaling on a 3-D axes object."""
    mins = points.min(axis=0)
    maxs = points.max(axis=0)
    centers = 0.5 * (mins + maxs)
    radius = 0.5 * float(np.max(maxs - mins))
    ax.set_xlim(centers[0] - radius, centers[0] + radius)
    ax.set_ylim(centers[1] - radius, centers[1] + radius)
    ax.set_zlim(centers[2] - radius, centers[2] + radius)
