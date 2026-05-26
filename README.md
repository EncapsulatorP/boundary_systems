# boundary_systems

Mathematical visualization of fractal surfaces with overlaid path trajectories.

Two scripts render 3D scatter plots of:
- **Mandelbulb** — the power-8 3D analogue of the Mandelbrot set, sampled via an escape-time boundary search.
- **Fermat surfaces** — the real locus of `|x|^n + |y|^n + |z|^n = 1`, solved analytically.

Paths are generated from arithmetic and space-filling sequences (prime gaps, nested radicals, Hilbert curves, Fibonacci spirals) and projected onto the surfaces to study how different generative algorithms cover 3D space.

## Files

| File | Description |
|------|-------------|
| `mandelbulb_core.py` | Shared primitives: escape test, surface sampling, signal utilities, densification |
| `mandelbulb_arithmetic_paths.py` | Z_p prime-compression and Pythagorean radical-tower paths over a Mandelbulb |
| `pathfilling.py` | Six path modes (fibonacci, hilbert, spiral, pythagorean, zp, all) over Mandelbulb or Fermat surfaces |

## Requirements

Python 3.10+

```bash
pip install numpy matplotlib
```

## Usage

**Arithmetic paths over a Mandelbulb:**
```bash
python mandelbulb_arithmetic_paths.py
python mandelbulb_arithmetic_paths.py --save bulb.png --no-show
python mandelbulb_arithmetic_paths.py --surface-samples 1400 --power 8
```

**Path-filling modes:**
```bash
python pathfilling.py
python pathfilling.py --path-mode hilbert --hilbert-order 5
python pathfilling.py --path-mode all --save pathfill.png --no-show
python pathfilling.py --surface-type fermat --fermat-degree 6 --path-mode all --save fermat6.png --no-show
```

Both scripts support `--help` for a full argument listing.

## Output images

Pre-rendered images are included:

| File | Description |
|------|-------------|
| `bulb.png` | Mandelbulb surface render |
| `aritmetic_paths_mandelbulbs.png` | Z_p and Pythagorean paths over a Mandelbulb |
| `fermat_paths.png` | Multiple path modes over a Fermat surface |
| `fermat_surface_hilbert.png` | Hilbert path on a Fermat surface |
| `path_filling_fermat_surface.png` | Fibonacci fill on a Fermat surface |
| `path_filling_fibonnaci.png` | Fibonacci fill on a Mandelbulb |
