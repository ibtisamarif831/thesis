# Feature-family visual audit

**Audit date:** 2026-07-27  
**Scope:** Visual review of all seven Feature Groups representatives across the B/W, Red, and Colored dashboard cohorts.

## Validation boundary

This is a systematic visual audit, not completed human validation. The frozen two-rater benchmark remains blocked with 900 unrated cells.

The audited full-corpus cohorts contain:

- **B/W:** 9,215 icons
- **Red:** 10 icons
- **Colored:** 19,524 icons

The Red cohort is too small and repetitive for strong conclusions. It consists mostly of basic signs, shapes, and color-like pictograms, with the China flag as the only more internally detailed example.

## Summary

| Family | Finding |
|---|---|
| Complexity | Grayscale quadtree failed cross-source face validity; Canny edge density is the replacement representative and requires continued visual review. |
| Shape/silhouette | Works as external-contour coverage, but it is not a reliable human closure measure and has a severe B/W ceiling. |
| Stroke/structure | Generally works as a global foreground-mass axis. It is not individual stroke orientation. Red validation is weak. |
| Density/fill | Works for thin versus erosion-resistant shapes, but thick line art can score like a filled icon. It has a strong B/W ceiling. |
| Balance/layout | Works for binary silhouette symmetry, but ignores internal color/detail and produces many perfect-score false positives. |
| Color/contrast | Strongest and clearest representative. Values visually match saturation across all three cohorts. |
| Texture | Not reliable as perceptual texture. Flat outlined scenes can receive the highest values. |

## 1. Complexity

**Representative:** `canny_edge_density`  
**Verdict:** Preferred over grayscale quadtree variability after a cross-source failure was identified.

### Visual findings

- The OpenMoji “french fries” icon scored 0.928 and the visually simple McDougall “Product” icon scored 0.866 under grayscale quadtree variability, above the more detailed ARASAAC “media” icon at 0.767.
- The corresponding edge densities are 0.047, 0.015, and 0.109, giving the visually plausible order: media, french fries, Product.
- Against all 239 currently extracted McDougall subjective-complexity ratings, Canny edge density reaches Spearman ρ = 0.556, compared with 0.382 for grayscale quadtree variability. The extracted ratings still require release-gate verification before this is treated as final validation.
- Forsythe et al. report Spearman ρ = .49 for Canny against McDougall human complexity ratings and explain that the connected dual thresholds suppress shading and noise.

### Why quadtree remains secondary

The quadtree measurement remains in the active 81-feature registry because it still describes grayscale structural subdivision. It is no longer used as the single human-facing Complexity representative because antialiasing, raster transitions, and color-to-luminance boundaries can dominate its value.

### Recommended “How to read it”

> Lower values indicate fewer detected edges across the canvas; higher values indicate more connected edge and detail structure. The extractor smooths before Canny edge detection to reduce isolated raster noise, but edge density remains an image proxy rather than a direct human-complexity judgment.

## 2. Shape/silhouette

**Representative:** `enclosure_score_v2`  
**Verdict:** The current description overstates closure.

### Visual findings

- Low values correctly identify thin or open structures; a single line scores 0.034.
- Red examples progress from the open spiral at 0.303 through the cross at 0.573 to the full rectangular China flag at 0.990.
- High values primarily mean that external contours cover the active box. They do not necessarily mean stronger human-perceived closure.
- 64.7% of B/W icons score at least 0.95, leaving weak separation in that cohort.
- Filled rectangles, flags, text blocks, and background-like regions can all approach 1.

### Recommended “How to read it”

> Lower values occur when external contours occupy little of the active box, as with thin, open, or fragmented marks. Higher values occur when external contours enclose and cover more of that box, as with large closed or filled forms. This is a contour-area proxy, not a direct measure of human Gestalt closure.

## 3. Stroke/structure

**Representative:** `principal_axis_orientation_v2`  
**Verdict:** Acceptable as a global axis, not as an amount or individual stroke direction.

### Visual findings

- Defined B/W and Colored examples generally follow the visible global axis.
- Approximately 30% of B/W and Colored icons are undefined because they do not have a sufficiently dominant axis.
- Six of the ten Red icons are undefined.
- The remaining Red sample includes two nearly identical splats at about 145° with confidence only 0.24.
- The formula uses PCA over all foreground pixels. It measures the orientation of the complete foreground distribution, not the direction of individual strokes.

### Recommended “How to read it”

> This is the dominant axis of the icon’s overall foreground distribution, not an amount and not necessarily the direction of individual strokes. 0° and 180° are horizontal, 90° is vertical, and intermediate values are diagonal. Confidence below 0.20 means that no reliable dominant axis was found.

## 4. Density/fill

**Representative:** `solid_fill_ratio_v2`  
**Verdict:** Useful but narrower than “filled versus outline.”

### Visual findings

- Red examples progress sensibly: outline circle 0.215, spiral 0.303, prohibition sign 0.439, solid cross 0.843, sphere 0.890, and flag 0.920.
- Colored examples also progress from thin-line scenes toward broad filled regions.
- 65.2% of B/W icons score at least 0.90.
- Thick line drawings can score very highly even though they remain outlines; a B/W hand glyph scores 0.946.
- The feature measures survival under erosion, combining stroke thickness and filled-area width. It does not directly classify filled versus outlined icons.

### Recommended “How to read it”

> The value reports how much foreground remains after erosion at three icon-relative scales. Lower values indicate thin or narrow marks that disappear quickly; higher values indicate thick strokes or broad filled regions that survive erosion. A thick outline can therefore receive a high value without being a fully filled silhouette.

## 5. Balance/layout

**Representative:** `horizontal_symmetry_v2`  
**Verdict:** Works only as binary silhouette correspondence and has substantial ceiling effects.

### Visual findings

- Red examples broadly progress from asymmetric spiral and splat shapes toward symmetric crosses, circles, and rectangles.
- Colored low and high extremes often look sensible.
- 69.8% of B/W, 40% of Red, and 18.7% of Colored icons receive exactly 1.
- A visually asymmetric “7” receives 1, showing that the two-pixel tolerance can be overly forgiving for some sparse forms.
- Colored rectangular backgrounds can dominate the mask and receive perfect symmetry even when the visible internal scene is asymmetric.
- The metric ignores color correspondence and internal tonal structure.

### Recommended “How to read it”

> Lower values indicate weaker left-right correspondence in the binary foreground silhouette; higher values indicate stronger overlap after allowing a two-pixel tolerance. Internal colors and details are ignored, and a large symmetric background or bounding shape can dominate the result.

## 6. Color/contrast

**Representative:** `mean_saturation_v2`  
**Verdict:** Visually reliable.

### Visual findings

- In B/W, 91% of icons have exactly 0 saturation and the maximum is only 0.063.
- Red values range from 0.787 to 0.973 and visually track saturation.
- In Colored, near-gray icons and icons with only tiny colored accents score low, while vivid solid colors reach 1.
- This is the strongest representative among the seven.
- It measures mean saturation only, not contrast, color count, hue diversity, or the complete Color/contrast family.

### Recommended “How to read it”

> Lower values indicate grayscale, near-grayscale, or muted foreground colors; higher values indicate more strongly saturated foreground color. The value is averaged across the foreground, so a small vivid accent can still produce a low overall score. It does not measure contrast or the number of colors.

## 7. Texture

**Representative:** `local_texture_variation_v2`  
**Verdict:** Currently unreliable as perceptual texture.

### Visual findings

- B/W geometric outlines titled “shapes” score 0.827 despite having no perceptual surface texture.
- A flat Colored “hydrotherapy” door scene scores the corpus maximum, 0.839.
- Both examples use confident alpha masks, so these failures come from the metric rather than foreground-mask failure.
- The 7×7 window has a three-pixel radius, while the foreground is eroded by only two pixels. The claim that the silhouette edge is excluded is therefore not strictly true.
- Internal object boundaries and nearby foreground/background transitions strongly raise the value.
- Red values mainly rank boundary geometry; none of the ten Red icons supplies convincing texture evidence.

### Recommended “How to read it” for the current implementation

> Lower values indicate little local luminance change around foreground pixels; higher values indicate stronger nearby light/dark variation. Internal boundaries, thin contours, and foreground/background transitions can also raise the value, so this is a local luminance-variation measure rather than a pure perceptual-texture score.

## Overall recommendation

- Retain Canny edge density as the current Complexity representative while continuing cross-dataset and two-rater validation.
- Retain Balance/layout only with its binary-silhouette and ceiling-effect limitations made explicit.
- Narrow the claims for Shape/silhouette and Density/fill. Consider replacing their representatives if the intended constructs are genuinely human closure and filled-versus-outline treatment.
- Do not present Texture as validated perceptual texture until the window/erosion behavior is repaired and the replacement is visually and human-rated.
- Do not draw strong family conclusions from the current ten-icon Red cohort.
