# Tamura Coarseness Validation

## Decision

`texture_coarseness` passed the pre-activation checks and is active as the 2nd representative of the Texture family, after `texture_entropy`.

## Literature basis

The source is:

> H. Tamura, S. Mori, and T. Yamawaki, "Textural Features Corresponding to Visual Perception," *IEEE Transactions on Systems, Man, and Cybernetics*, 8(6), 460-473, 1978. DOI: `10.1109/TSMC.1978.4309999`.

The verified local paper is `papers/Tamura-Textural_Features_Corresponding_to_Visual_Perception.pdf`.

On pages 465-466, the authors define coarseness by:

1. Computing local averages at power-of-two neighborhood sizes.
2. Comparing non-overlapping averages on opposite sides of each point, horizontally and vertically.
3. Selecting the best size from the strongest difference response.
4. Averaging the best sizes over the effective picture.

The paper's refinement chooses the largest scale whose response is at least `t` times the maximum response. The reported stable setting is approximately `t = 0.9`.

## Glyph adaptation

The original method assumes rectangular 128x128 texture samples. The repository contains isolated glyphs on a larger canvas, so exterior canvas whitespace must not define texture coarseness.

The implementation therefore:

- Uses the foreground bounding box as the effective picture.
- Scales its longest side to 128 pixels without changing aspect ratio.
- Uses power-of-two operators up to 32 pixels.
- Uses the paper's `t = 0.9` near-maximum rule.
- Evaluates only positions supported by every available scale, matching the paper's boundary-strip warning.
- Divides the average best size by the largest available operator size, producing a comparable normalized score.

This is a documented glyph adaptation of Tamura coarseness, not a claim that isolated icons are full natural-texture fields.

## Validation sample

Validation used all 1,038 rows in `icon_data/analysis/features.csv`.

| Check | Result |
|---|---:|
| Valid values | 1,038 / 1,038 |
| Missing values | 0 |
| Standard deviation | 0.178126 |
| Variance | 0.031729 |
| Distinct values rounded to 6 decimals | 1,030 |
| Minimum | 0.131944 |
| Median | 0.553370 |
| Maximum | 1.000000 |
| Spearman correlation with `texture_entropy` | -0.028712 |
| Absolute Spearman correlation with `texture_entropy` | 0.028712 |

The pair is far below the selection limit `|rho| < 0.70`.

The strongest correlation with another active feature in the preserved 1,038-row analysis sample was the inverse relationship with `canny_edge_density`, `rho = -0.553500`. This is moderate rather than redundant and is directionally sensible: fine, repeated detail tends to create more edges, while coarse simple fields create fewer.

## Visual audit

Lowest-scoring examples included:

- USP multi-panel instruction pictograms.
- ISO sterile labels containing repeated letters and compartment boundaries.
- A dense binary-file pattern.

Highest-scoring examples included:

- A simple bus silhouette.
- A large envelope field.
- Blanket, bookmark, bottle, cross, and two-dot glyphs dominated by large simple elements.

The ordering matches the intended fine-to-coarse interpretation and does not reproduce entropy's tonal-variety ordering.

## Tests

`code/tests/test_texture_coarseness.py` verifies:

- Empty-foreground behavior.
- Largest-scale selection for a uniform effective picture.
- Higher coarseness for coarse versus fine checkerboards.
- Invariance to exterior canvas whitespace.

Run:

```bash
/Users/macbook/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -m unittest discover -s code/tests -p 'test_*.py'
```

## Limitation

This feature measures the spatial scale of intensity structure inside the glyph's effective bounding-box picture. It should be interpreted as fine versus coarse glyph texture/pattern, not as semantic material roughness.
