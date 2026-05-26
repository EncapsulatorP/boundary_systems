#!/usr/bin/env python3
"""
Visualize p-adic packet drift (Witt–Teichmüller carry diagnostics) over
arithmetic digit sequences.

Two panels
----------
Left:   Drift depth Δ_p(n, L) vs rank n at a fixed window length L,
        shown for both the prime sequence and the Pythagorean tower sequence.
        Scatter markers are coloured by the Teichmüller label.

Right:  Heatmap of Δ_p(n, L) over varying (rank, window-length) for the
        prime digit sequence. Each row is a window length, each column a
        start rank. Bright = deep (stable); dark = shallow (drifting).

Digit sequences
---------------
- Primes:   first N odd primes concatenated in base p.
- Pythagorean: floor(y_k * scale) for y_k = 2 - 2*cos(pi/2^k),
              concatenated in base p.

Examples
--------
python padic_viz.py
python padic_viz.py --p 5 --L 4 --sequence-length 80
python padic_viz.py --p 3 --max-L 8 --save outputs/padic_drift.png --no-show
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path

import numpy as np

from mandelbulb_core import odd_primes
from padic_drift import carry_diagnostic, scan_drift, sequence_to_digits

import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap


# ---------------------------------------------------------------------------
# Sequence builders
# ---------------------------------------------------------------------------

def pythagorean_tower_ints(n: int, scale: int = 10 ** 7) -> list[int]:
    """
    Return floor(y_k * scale) for y_k = 2 - 2*cos(pi / 2^k), k = 1..n.
    The scaling converts the rapidly-shrinking real values to non-trivial integers.
    """
    values = []
    for k in range(1, n + 1):
        y = 2.0 - 2.0 * math.cos(math.pi / (2 ** k))
        values.append(max(1, int(y * scale)))
    return values


# ---------------------------------------------------------------------------
# Heatmap builder
# ---------------------------------------------------------------------------

def drift_heatmap(digits: list[int], p: int, max_L: int) -> np.ndarray:
    """
    Grid of drift depths Δ_p(n, L) with shape (max_L - 1, N).
    Row 0 corresponds to L=2; row max_L-2 to L=max_L.
    NaN where the packet is 0 or the window overruns the sequence.
    """
    N = len(digits)
    grid = np.full((max_L - 1, N), np.nan)
    for L in range(2, max_L + 1):
        for n in range(N - L + 1):
            d = carry_diagnostic(digits, n, L, p)
            if d is not None:
                grid[L - 2, n] = d.drift
    return grid


# ---------------------------------------------------------------------------
# Visualisation
# ---------------------------------------------------------------------------

def plot_scene(
    prime_digits: list[int],
    tower_digits: list[int],
    p: int,
    L: int,
    max_L: int,
    args: argparse.Namespace,
) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(14, 6), constrained_layout=True)
    fig.patch.set_facecolor("#05070a")
    for ax in axes:
        ax.set_facecolor("#0d1117")

    # ---- Left panel: drift depth vs rank at fixed L -------------------------
    ax = axes[0]

    prime_scan = scan_drift(prime_digits, L, p)
    tower_scan = scan_drift(tower_digits, L, p)

    def _draw_scan(scan, line_color, cmap_name, label):
        if not scan:
            return
        ns = [d.n for d in scan]
        deltas = [d.drift for d in scan]
        labels = [d.teichmuller for d in scan]
        ax.plot(ns, deltas, color=line_color, linewidth=1.3, alpha=0.7)
        ax.scatter(
            ns, deltas,
            c=labels,
            cmap=cmap_name,
            s=26,
            alpha=0.9,
            zorder=3,
            label=label,
        )

    _draw_scan(prime_scan,  "#ff6b6b", "autumn", "Primes")
    _draw_scan(tower_scan,  "#74c0fc", "winter", "Pythagorean tower")

    ax.set_xlabel("rank n", color="#d7dee9")
    ax.set_ylabel(f"drift depth  Δ_{p}(n, L={L})", color="#d7dee9")
    ax.set_title(
        f"p-adic packet drift  (p={p}, L={L})\n"
        "markers coloured by Teichmüller label",
        color="#f4f7fb",
        pad=10,
    )
    ax.tick_params(colors="#b3c1d1")
    for spine in ax.spines.values():
        spine.set_edgecolor("#2a3a4a")
    legend = ax.legend(facecolor="#0a0f14", edgecolor="#0a0f14")
    for txt in legend.get_texts():
        txt.set_color("#f4f7fb")

    # ---- Right panel: heatmap over (n, L) for primes -----------------------
    ax = axes[1]
    hmap = drift_heatmap(prime_digits, p, max_L)

    cmap = LinearSegmentedColormap.from_list(
        "drift",
        ["#061017", "#1572a1", "#19a7ce", "#f6bd60", "#f28482"],
    )
    im = ax.imshow(
        hmap,
        aspect="auto",
        origin="lower",
        cmap=cmap,
        interpolation="nearest",
    )
    ax.set_xlabel("rank n", color="#d7dee9")
    ax.set_ylabel("window length L", color="#d7dee9")
    ax.set_yticks(range(max_L - 1))
    ax.set_yticklabels(range(2, max_L + 1))
    ax.set_title(
        f"Drift heatmap — primes, p={p}\n"
        "bright = deep/stable,  dark = shallow/drifting",
        color="#f4f7fb",
        pad=10,
    )
    ax.tick_params(colors="#b3c1d1")
    for spine in ax.spines.values():
        spine.set_edgecolor("#2a3a4a")

    cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label(f"Δ_{p}(n, L)", color="#d7dee9")
    cbar.ax.yaxis.set_tick_params(color="#b3c1d1")
    plt.setp(cbar.ax.yaxis.get_ticklabels(), color="#b3c1d1")

    fig.suptitle(
        "Witt–Teichmüller Carry Drift  ·  C_p(n, L) = (carry depth, residue, drift depth)",
        color="#f4f7fb",
        fontsize=11,
    )

    if args.save:
        fig.savefig(args.save, dpi=args.dpi, facecolor=fig.get_facecolor())
    if not args.no_show:
        plt.show()
    plt.close(fig)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Visualize p-adic packet drift over arithmetic digit sequences."
    )
    parser.add_argument(
        "--p", type=int, default=3,
        help="Prime base for p-adic analysis (default: 3).",
    )
    parser.add_argument(
        "--L", type=int, default=3,
        help="Fixed window length shown in the left (line) panel.",
    )
    parser.add_argument(
        "--max-L", type=int, default=7,
        help="Maximum window length in the right (heatmap) panel.",
    )
    parser.add_argument(
        "--sequence-length", type=int, default=60,
        help="Number of integers in each source sequence before digit expansion.",
    )
    parser.add_argument(
        "--tower-scale", type=int, default=10 ** 7,
        help="Integer scaling factor applied to Pythagorean tower values.",
    )
    parser.add_argument("--dpi", type=int, default=180, help="Saved image DPI.")
    parser.add_argument("--save", type=Path, default=None, help="Optional output path.")
    parser.add_argument(
        "--no-show", action="store_true",
        help="Do not open an interactive window.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    p = args.p
    N = args.sequence_length

    primes = odd_primes(N)
    tower = pythagorean_tower_ints(N, scale=args.tower_scale)

    prime_digits = sequence_to_digits(primes, p)
    tower_digits = sequence_to_digits(tower, p)

    plot_scene(prime_digits, tower_digits, p, args.L, args.max_L, args)


if __name__ == "__main__":
    main()
