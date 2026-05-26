#!/usr/bin/env python3
"""
Render path-filling trajectories over a Mandelbulb surface.

This script is aimed at the follow-up question:
what fills the Mandelbulb surface well if you do not use the Mandelbrot /
Mandelbulb iteration itself as the path generator?

Implemented modes
-----------------
- fibonacci: near-uniform coverage via Fibonacci sphere ordering
- hilbert: continuous Hilbert path mapped from a square to the sphere
- spiral: smooth spherical sweep
- pythagorean: arithmetic tower path, included for comparison
- zp: odd-prime compression path, included for comparison
- all: overlay the major modes together

Surfaces
--------
- mandelbulb: sampled numerically via escape-time boundary search
- fermat: analytic real Fermat-type surface ``|x|^n + |y|^n + |z|^n = 1``

Examples
--------
python pathfilling.py
python pathfilling.py --path-mode hilbert --hilbert-order 5
python pathfilling.py --surface-type fermat --fermat-degree 6 --path-mode all
python pathfilling.py --path-mode all --save pathfill.png --no-show
"""

from __future__ import annotations

import argparse
import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from mandelbulb_core import (
    MandelbulbConfig,
    approximate_mandelbulb_surface_radius,
    densify_angles,
    densify_directions,
    fibonacci_sphere,
    normalise,
    odd_primes,
    set_equal_axes,
)

import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap


@dataclass(frozen=True)
class PathSpec:
    label: str
    directions: np.ndarray
    hover: np.ndarray
    color: str
    marker_cmap: str


def approximate_fermat_surface_radius(direction: np.ndarray, degree: float) -> tuple[float, int]:
    direction = direction / np.linalg.norm(direction)
    denom = float(np.sum(np.abs(direction) ** degree))
    if denom == 0.0:
        return 0.0, 1
    radius = (1.0 / denom) ** (1.0 / degree)
    return radius, 1


def approximate_surface_radius(
    direction: np.ndarray,
    cfg: MandelbulbConfig,
    surface_type: str,
    fermat_degree: float,
) -> tuple[float, int]:
    if surface_type == "mandelbulb":
        return approximate_mandelbulb_surface_radius(direction, cfg)
    if surface_type == "fermat":
        return approximate_fermat_surface_radius(direction, fermat_degree)
    raise ValueError(f"Unsupported surface type: {surface_type}")


def sample_surface(
    samples: int,
    cfg: MandelbulbConfig,
    surface_type: str,
    fermat_degree: float,
) -> tuple[np.ndarray, np.ndarray]:
    directions = fibonacci_sphere(samples)
    points = np.zeros((samples, 3), dtype=float)
    colors = np.zeros(samples, dtype=float)

    for idx, direction in enumerate(directions):
        radius, escape_iter = approximate_surface_radius(
            direction, cfg, surface_type, fermat_degree
        )
        points[idx] = direction * radius
        colors[idx] = radius + 0.025 * escape_iter

    return points, colors


def build_fibonacci_path(points: int) -> PathSpec:
    directions = fibonacci_sphere(points)
    hover = np.full(points, 0.024, dtype=float)
    directions, hover = densify_directions(directions, hover, factor=3)
    return PathSpec(
        label="Fibonacci fill",
        directions=directions,
        hover=hover,
        color="#ff6b6b",
        marker_cmap="autumn",
    )


def build_spiral_path(points: int, turns: float) -> PathSpec:
    t = np.linspace(0.0, 1.0, points)
    z = 0.98 - 1.96 * t
    theta = turns * 2.0 * math.pi * t
    radius = np.sqrt(np.maximum(0.0, 1.0 - z * z))
    directions = np.column_stack((np.cos(theta) * radius, np.sin(theta) * radius, z))
    hover = 0.02 + 0.01 * np.sin(2.0 * theta) ** 2
    directions, hover = densify_directions(directions, hover, factor=4)
    return PathSpec(
        label="Spiral sweep",
        directions=directions,
        hover=hover,
        color="#7cf29c",
        marker_cmap="summer",
    )


def build_pythagorean_path(points: int) -> PathSpec:
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
    hover = 0.028 + 0.085 * defect_n
    directions, hover = densify_angles(theta, phi, hover, factor=4)
    return PathSpec(
        label="Pythagorean tower",
        directions=directions,
        hover=hover,
        color="#8ce99a",
        marker_cmap="YlGn",
    )


def build_zp_path(points: int) -> PathSpec:
    primes = np.asarray(odd_primes(points), dtype=float)
    compression = np.log(primes - 1.0)
    gaps = np.diff(np.concatenate(([2.0], primes)))

    compression_n = normalise(compression)
    gap_n = normalise(np.log1p(gaps))
    t = np.linspace(0.0, 1.0, points)

    theta = 6.0 * math.pi * t + 0.8 * math.pi * gap_n
    phi = 0.22 * math.pi + 0.56 * math.pi * compression_n
    hover = 0.03 + 0.08 * gap_n
    directions, hover = densify_angles(theta, phi, hover, factor=4)
    return PathSpec(
        label="Z_p proxy path",
        directions=directions,
        hover=hover,
        color="#f08c00",
        marker_cmap="Wistia",
    )


def rot(n: int, x: int, y: int, rx: int, ry: int) -> tuple[int, int]:
    if ry == 0:
        if rx == 1:
            x = n - 1 - x
            y = n - 1 - y
        x, y = y, x
    return x, y


def d2xy(order: int, d: int) -> tuple[int, int]:
    n = 1 << order
    x = 0
    y = 0
    t = d
    s = 1
    while s < n:
        rx = 1 & (t // 2)
        ry = 1 & (t ^ rx)
        x, y = rot(s, x, y, rx, ry)
        x += s * rx
        y += s * ry
        t //= 4
        s *= 2
    return x, y


def build_hilbert_path(order: int) -> PathSpec:
    side = 1 << order
    total = side * side
    coords = np.zeros((total, 2), dtype=float)
    for d in range(total):
        x, y = d2xy(order, d)
        coords[d] = (x, y)
    u = (coords[:, 0] + 0.5) / side
    v = (coords[:, 1] + 0.5) / side
    lon = 2.0 * math.pi * (u - 0.5)
    z = 1.0 - 2.0 * v
    radius = np.sqrt(np.maximum(0.0, 1.0 - z * z))
    directions = np.column_stack((np.cos(lon) * radius, np.sin(lon) * radius, z))
    hover = np.full(total, 0.022, dtype=float)
    directions, hover = densify_directions(directions, hover, factor=2)
    return PathSpec(
        label=f"Hilbert fill (order {order})",
        directions=directions,
        hover=hover,
        color="#74c0fc",
        marker_cmap="winter",
    )


def project_path_onto_surface(
    directions: np.ndarray,
    hover: np.ndarray,
    cfg: MandelbulbConfig,
    surface_type: str,
    fermat_degree: float,
) -> np.ndarray:
    path = np.zeros_like(directions)
    for idx, direction in enumerate(directions):
        radius, _ = approximate_surface_radius(
            direction, cfg, surface_type, fermat_degree
        )
        path[idx] = direction * (radius * (1.0 + hover[idx]))
    return path


def approximate_polyline_length(path: np.ndarray) -> float:
    if len(path) < 2:
        return 0.0
    return float(np.linalg.norm(np.diff(path, axis=0), axis=1).sum())


def make_colormap() -> LinearSegmentedColormap:
    return LinearSegmentedColormap.from_list(
        "mandelbulb_pathfill",
        ["#061017", "#1572a1", "#2cb7d9", "#f6bd60", "#f28482"],
    )


def surface_display_name(surface_type: str, fermat_degree: float) -> str:
    if surface_type == "mandelbulb":
        return "Mandelbulb"
    if surface_type == "fermat":
        degree_label = int(fermat_degree) if float(fermat_degree).is_integer() else fermat_degree
        return f"Fermat Surface (n={degree_label})"
    return surface_type


def build_path_specs(args: argparse.Namespace) -> list[PathSpec]:
    if args.path_mode == "all":
        return [
            build_fibonacci_path(args.path_points),
            build_hilbert_path(args.hilbert_order),
            build_spiral_path(args.path_points, args.spiral_turns),
            build_pythagorean_path(args.path_points),
        ]
    if args.path_mode == "fibonacci":
        return [build_fibonacci_path(args.path_points)]
    if args.path_mode == "hilbert":
        return [build_hilbert_path(args.hilbert_order)]
    if args.path_mode == "spiral":
        return [build_spiral_path(args.path_points, args.spiral_turns)]
    if args.path_mode == "pythagorean":
        return [build_pythagorean_path(args.path_points)]
    if args.path_mode == "zp":
        return [build_zp_path(args.path_points)]
    raise ValueError(f"Unsupported path mode: {args.path_mode}")


def plot_scene(
    surface_points: np.ndarray,
    surface_colors: np.ndarray,
    projected_specs: list[tuple[PathSpec, np.ndarray]],
    args: argparse.Namespace,
) -> None:
    fig = plt.figure(figsize=(12, 10), constrained_layout=True)
    ax = fig.add_subplot(111, projection="3d")
    fig.patch.set_facecolor("#05070a")
    ax.set_facecolor("#05070a")
    ax.set_box_aspect((1.0, 1.0, 1.0))

    ax.scatter(
        surface_points[:, 0],
        surface_points[:, 1],
        surface_points[:, 2],
        c=surface_colors,
        cmap=make_colormap(),
        s=args.surface_point_size,
        alpha=0.7,
        linewidths=0,
    )

    combined = [surface_points]
    for spec, path in projected_specs:
        ax.plot(
            path[:, 0],
            path[:, 1],
            path[:, 2],
            color=spec.color,
            linewidth=2.35,
            alpha=0.97,
            label=f"{spec.label} | L~{approximate_polyline_length(path):.2f}",
        )
        ax.scatter(
            path[:, 0],
            path[:, 1],
            path[:, 2],
            c=np.linspace(0.0, 1.0, len(path)),
            cmap=spec.marker_cmap,
            s=10 if len(path) > 400 else 18,
            alpha=0.9,
        )
        combined.append(path)

    set_equal_axes(ax, np.vstack(combined))
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
        f"Path Filling Over a {surface_display_name(args.surface_type, args.fermat_degree)}\n"
        f"Mode: {args.path_mode}",
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
        description="Plot path-filling trajectories over Mandelbulb or Fermat surfaces."
    )
    parser.add_argument(
        "--surface-type",
        choices=["mandelbulb", "fermat"],
        default="mandelbulb",
        help="Base surface to project the paths onto.",
    )
    parser.add_argument(
        "--fermat-degree",
        type=float,
        default=4.0,
        help="Degree n for the real Fermat surface |x|^n + |y|^n + |z|^n = 1.",
    )
    parser.add_argument(
        "--path-mode",
        choices=["fibonacci", "hilbert", "spiral", "pythagorean", "zp", "all"],
        default="fibonacci",
        help="Path generator to project onto the surface.",
    )
    parser.add_argument("--power", type=int, default=8, help="Mandelbulb power.")
    parser.add_argument("--max-iter", type=int, default=18, help="Escape iterations.")
    parser.add_argument(
        "--surface-samples",
        type=int,
        default=900,
        help="Number of directions used to sample the surface.",
    )
    parser.add_argument(
        "--path-points",
        type=int,
        default=48,
        help="Base control points for fibonacci, spiral, pythagorean, and zp modes.",
    )
    parser.add_argument(
        "--hilbert-order",
        type=int,
        default=4,
        help="Hilbert order. Total control points are 4**order.",
    )
    parser.add_argument(
        "--spiral-turns",
        type=float,
        default=11.0,
        help="Number of turns for the spiral sweep.",
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
    parser.add_argument("--elev", type=float, default=22.0, help="Camera elevation.")
    parser.add_argument("--azim", type=float, default=34.0, help="Camera azimuth.")
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
    if args.fermat_degree <= 0.0:
        raise ValueError("--fermat-degree must be positive.")
    cfg = MandelbulbConfig(
        power=args.power,
        max_iter=args.max_iter,
        search_radius=args.search_radius,
        radial_steps=args.radial_steps,
        refine_steps=args.refine_steps,
    )

    surface_points, surface_colors = sample_surface(
        args.surface_samples,
        cfg,
        args.surface_type,
        args.fermat_degree,
    )
    projected_specs: list[tuple[PathSpec, np.ndarray]] = []
    for spec in build_path_specs(args):
        path = project_path_onto_surface(
            spec.directions,
            spec.hover,
            cfg,
            args.surface_type,
            args.fermat_degree,
        )
        projected_specs.append((spec, path))

    plot_scene(surface_points, surface_colors, projected_specs, args)


if __name__ == "__main__":
    main()
