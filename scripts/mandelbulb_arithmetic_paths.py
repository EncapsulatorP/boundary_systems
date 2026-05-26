#!/usr/bin/env python3
"""
Render a Mandelbulb surface and overlay two arithmetic path families:

1. A ``Z_p``-inspired odd-prime path using the compression signal
   ``x_p = log(p - 1)`` as a visualization proxy.
2. A Pythagorean radical-tower path using
   ``y_n = 2 - 2 cos(pi / 2**n)`` together with the nested radical
   convergence defect.

This is a visualization script, not a canonical embedding theorem.
It follows the spirit of the user's thread: arithmetic signals are used
as structured paths over a Mandelbulb-like body.

Examples
--------
python mandelbulb_arithmetic_paths.py
python mandelbulb_arithmetic_paths.py --save bulb.png --no-show
python mandelbulb_arithmetic_paths.py --surface-samples 1400 --power 8
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path

import numpy as np

from mandelbulb_core import (
    MandelbulbConfig,
    approximate_mandelbulb_surface_radius,
    densify_angles,
    fibonacci_sphere,
    normalise,
    odd_primes,
    set_equal_axes,
)

import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap


def sample_surface(samples: int, cfg: MandelbulbConfig) -> tuple[np.ndarray, np.ndarray]:
    directions = fibonacci_sphere(samples)
    points = np.zeros((samples, 3), dtype=float)
    colors = np.zeros(samples, dtype=float)

    for idx, direction in enumerate(directions):
        radius, escape_iter = approximate_mandelbulb_surface_radius(direction, cfg)
        points[idx] = direction * radius
        colors[idx] = radius + 0.025 * escape_iter

    return points, colors


def build_zp_path_directions(points: int) -> tuple[np.ndarray, np.ndarray]:
    """
    Build directions from an odd-prime compression signal.

    There is no canonical ``Z_p -> R^3`` mapping in this context, so the script
    uses the thread's suggested compression idea ``log(Z(p) - 1)`` with the
    pragmatic proxy ``Z(p) = p``.
    """
    primes = np.asarray(odd_primes(points), dtype=float)
    compression = np.log(primes - 1.0)
    gaps = np.diff(np.concatenate(([2.0], primes)))

    compression_n = normalise(compression)
    gap_n = normalise(np.log1p(gaps))
    t = np.linspace(0.0, 1.0, points)

    theta = 6.0 * math.pi * t + 0.8 * math.pi * gap_n
    phi = 0.22 * math.pi + 0.56 * math.pi * compression_n
    hover = 0.03 + 0.08 * gap_n

    return densify_angles(theta, phi, hover, factor=5)


def build_pythagorean_path_directions(points: int) -> tuple[np.ndarray, np.ndarray]:
    """
    Build directions from the nested-radical Pythagorean tower signal.

    Uses:
    y_n = 2 - 2*cos(pi / 2**n)
    radical_n = sqrt(2 + radical_{n-1})
    """
    depths = np.arange(1, points + 1, dtype=float)
    tower_signal = 2.0 - 2.0 * np.cos(np.pi / (2.0**depths))

    radical_values = np.zeros(points, dtype=float)
    radical = 0.0
    for idx in range(points):
        radical = math.sqrt(2.0 + radical)
        radical_values[idx] = radical
    defect = 2.0 - radical_values

    signal_n = normalise(np.log1p(tower_signal))
    defect_n = normalise(np.log1p(defect[::-1]))[::-1]
    t = np.linspace(0.0, 1.0, points)

    theta = 4.5 * math.pi * t - 0.65 * math.pi * signal_n
    phi = 0.16 * math.pi + 0.58 * math.pi * (1.0 - defect_n)
    hover = 0.025 + 0.09 * defect_n

    return densify_angles(theta, phi, hover, factor=5)


def project_path_onto_surface(
    directions: np.ndarray, hover: np.ndarray, cfg: MandelbulbConfig
) -> np.ndarray:
    path = np.zeros_like(directions)
    for idx, direction in enumerate(directions):
        radius, _ = approximate_mandelbulb_surface_radius(direction, cfg)
        path[idx] = direction * (radius * (1.0 + hover[idx]))
    return path


def make_colormap() -> LinearSegmentedColormap:
    return LinearSegmentedColormap.from_list(
        "mandelbulb_arithmetic",
        ["#0a0f14", "#146c94", "#19a7ce", "#f6bd60", "#f28482"],
    )


def plot_scene(
    surface_points: np.ndarray,
    surface_colors: np.ndarray,
    zp_path: np.ndarray,
    tower_path: np.ndarray,
    args: argparse.Namespace,
) -> None:
    fig = plt.figure(figsize=(12, 10), constrained_layout=True)
    ax = fig.add_subplot(111, projection="3d")
    fig.patch.set_facecolor("#05070a")
    ax.set_facecolor("#05070a")
    ax.set_box_aspect((1.0, 1.0, 1.0))

    cmap = make_colormap()
    ax.scatter(
        surface_points[:, 0],
        surface_points[:, 1],
        surface_points[:, 2],
        c=surface_colors,
        cmap=cmap,
        s=args.surface_point_size,
        alpha=0.72,
        linewidths=0,
    )

    ax.plot(
        zp_path[:, 0],
        zp_path[:, 1],
        zp_path[:, 2],
        color="#ff5f5d",
        linewidth=2.4,
        alpha=0.95,
        label="Z_p odd-prime path",
    )
    ax.scatter(
        zp_path[:, 0],
        zp_path[:, 1],
        zp_path[:, 2],
        c=np.linspace(0.0, 1.0, len(zp_path)),
        cmap="autumn",
        s=22,
        alpha=0.95,
    )

    ax.plot(
        tower_path[:, 0],
        tower_path[:, 1],
        tower_path[:, 2],
        color="#7cf29c",
        linewidth=2.4,
        alpha=0.95,
        label="Pythagorean tower path",
    )
    ax.scatter(
        tower_path[:, 0],
        tower_path[:, 1],
        tower_path[:, 2],
        c=np.linspace(0.0, 1.0, len(tower_path)),
        cmap="summer",
        s=22,
        alpha=0.95,
    )

    combined = np.vstack([surface_points, zp_path, tower_path])
    set_equal_axes(ax, combined)
    ax.set_xlabel("x", color="#d7dee9", labelpad=10)
    ax.set_ylabel("y", color="#d7dee9", labelpad=10)
    ax.set_zlabel("z", color="#d7dee9", labelpad=10)
    ax.tick_params(colors="#b3c1d1")
    ax.grid(False)
    for axis in (ax.xaxis, ax.yaxis, ax.zaxis):
        axis.pane.fill = False
        axis.pane.set_edgecolor((0.85, 0.9, 0.96, 0.16))
    ax.view_init(elev=args.elev, azim=args.azim)
    ax.set_title(
        "Arithmetic Paths Over a Mandelbulb\n"
        "Z_p compression and Pythagorean radical-tower projections",
        color="#f4f7fb",
        pad=16,
    )
    legend = ax.legend(loc="upper left", facecolor="#0a0f14", edgecolor="#0a0f14")
    for text in legend.get_texts():
        text.set_color("#f4f7fb")

    if args.save:
        fig.savefig(args.save, dpi=args.dpi, facecolor=fig.get_facecolor())
    if not args.no_show:
        plt.show()
    plt.close(fig)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Plot a Mandelbulb with overlaid Z_p and Pythagorean tower paths."
    )
    parser.add_argument("--power", type=int, default=8, help="Mandelbulb power.")
    parser.add_argument(
        "--max-iter", type=int, default=18, help="Escape iterations per sample."
    )
    parser.add_argument(
        "--surface-samples",
        type=int,
        default=900,
        help="Number of radial directions used to sample the bulb surface.",
    )
    parser.add_argument(
        "--path-points",
        type=int,
        default=33,
        help="Number of points per arithmetic path.",
    )
    parser.add_argument(
        "--search-radius",
        type=float,
        default=1.9,
        help="Outer radius used to search for the Mandelbulb boundary.",
    )
    parser.add_argument(
        "--radial-steps",
        type=int,
        default=48,
        help="Coarse boundary search steps along each ray.",
    )
    parser.add_argument(
        "--refine-steps",
        type=int,
        default=7,
        help="Binary-search refinement steps once the surface is bracketed.",
    )
    parser.add_argument("--elev", type=float, default=24.0, help="Camera elevation.")
    parser.add_argument("--azim", type=float, default=36.0, help="Camera azimuth.")
    parser.add_argument(
        "--surface-point-size",
        type=float,
        default=5.0,
        help="Scatter size for surface points.",
    )
    parser.add_argument("--dpi", type=int, default=180, help="Saved image DPI.")
    parser.add_argument("--save", type=Path, default=None, help="Optional output image.")
    parser.add_argument(
        "--no-show",
        action="store_true",
        help="Do not open a window; useful when saving in a headless session.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    cfg = MandelbulbConfig(
        power=args.power,
        max_iter=args.max_iter,
        search_radius=args.search_radius,
        radial_steps=args.radial_steps,
        refine_steps=args.refine_steps,
    )

    surface_points, surface_colors = sample_surface(args.surface_samples, cfg)
    zp_directions, zp_hover = build_zp_path_directions(args.path_points)
    tower_directions, tower_hover = build_pythagorean_path_directions(args.path_points)
    zp_path = project_path_onto_surface(zp_directions, zp_hover, cfg)
    tower_path = project_path_onto_surface(tower_directions, tower_hover, cfg)
    plot_scene(surface_points, surface_colors, zp_path, tower_path, args)


if __name__ == "__main__":
    main()
