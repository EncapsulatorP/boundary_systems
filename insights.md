# Insights

## Surface geometry

### Mandelbulb
The power-8 Mandelbulb is the most commonly studied 3D analogue of the Mandelbrot set, obtained by applying the escape-time iteration in spherical coordinates:

```
r^n * (sin(n*phi)*cos(n*theta), sin(n*phi)*sin(n*theta), cos(n*phi))
```

The boundary is found per direction via a coarse linear probe (48 steps) followed by a 7-step binary search — enough precision for path projection but not for high-resolution rendering. The coloring mixes escape radius and escape iteration to produce the warm-to-cool gradient across the fractal boundary.

### Fermat surface
The real Fermat surface `|x|^n + |y|^n + |z|^n = 1` has an analytic solution for the boundary radius along any unit direction `d`:

```
r = (sum(|d_i|^n))^(-1/n)
```

This is orders of magnitude faster than the Mandelbulb boundary search and produces smooth, convex shapes. At `n=2` the surface is the unit sphere; large `n` converges toward a cube. Paths on Fermat surfaces are easier to read visually because the surface has no concavities to hide segments.

## Path generators

### Fibonacci fill
Golden-angle ordering of the sphere gives near-uniform point density with no visible clustering. It is the most effective single-path fill in terms of coverage uniformity for a fixed point count.

### Hilbert path
A 2D Hilbert curve of order `k` covers a `4^k`-point grid, which is unwrapped onto the sphere via a longitude/latitude mapping. The curve is space-filling in 2D but the projection introduces non-uniform density — equatorial regions are oversampled relative to the poles. Order 4 (256 points) shows a clear space-filling structure; order 5 (1024 points) approaches uniform coverage at the cost of significant render time on the Mandelbulb.

### Spiral sweep
A constant-pitch spherical spiral parametrized by `z = 0.98 - 1.96*t`. Coverage becomes denser near the poles and sparser at mid-latitudes for a fixed turn count. The current implementation deliberately stops at `z = ±0.98` to avoid degenerate polar segments.

### Pythagorean tower path
Uses the nested-radical defect `2 - sqrt(2 + sqrt(2 + ...))` and the cosine signal `2 - 2*cos(pi/2^n)` to modulate azimuth and elevation. The sequence converges rapidly toward 2, so the path is concentrated at low depths and spreads thinly at large `n`. The defect drives the hover offset, lifting the path slightly above the surface as it converges.

### Z_p compression path
Uses `log(p - 1)` as a compression proxy for the prime `p`, with prime gaps modulating the azimuth. The resulting path is deliberately irregular: large prime gaps produce visible jumps that expose the gap structure visually. This irregularity distinguishes it from every other path mode, which are all smooth.

## Key observations

- **Polyline length as a coverage proxy**: `pathfilling.py` reports path length `L` in the legend. A larger `L` for the same number of control points generally indicates better coverage, though it also depends on how evenly the length is distributed.

- **Fibonacci dominates for uniform coverage**: Among the paths, Fibonacci sphere ordering consistently produces the most uniform scatter. The Hilbert path approaches similar uniformity only at order 5+, which multiplies point count by 4×.

- **Fermat surfaces isolate path geometry**: Because Fermat surfaces are convex and smooth, all paths are fully visible from any camera angle. The Mandelbulb's concavities can hide portions of a path, making Fermat a cleaner substrate for comparing path shapes.

- **Arithmetic paths are sparse by design**: The Z_p and Pythagorean paths use only ~30–50 control points. They are not meant to fill the surface — they are meant to trace a structured arithmetic signal over it. The densification step interpolates between control points to produce a smooth curve, but the underlying signal still determines the path's global shape.

- **Power parameter sensitivity**: The Mandelbulb changes shape significantly between `--power 4` (rounder, fewer lobes) and `--power 8` (canonical, complex boundary). Paths projected at `power 8` can look very different from the same paths at `power 4` because the boundary radius varies more sharply with direction.
