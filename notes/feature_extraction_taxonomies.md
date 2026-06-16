No. They are a mix of **paper-derived metrics** and **implementation proxies**.

**Directly from Forsythe et al.**
These are explicitly in *Measuring Icon Complexity: An Automated Analysis*:

- foreground area / foreground amount
- number of objects, which maps to connected components
- number of holes
- perimeter / edge measures
- Canny edge detection
- quadtree structural variability

**From Garcia et al.**
Garcia’s abstractness metric is component-count based, including:

- closed figures
- open figures
- letters
- special characters
- horizontal / vertical / diagonal lines
- arrowheads
- arcs

So `connected components`, `contour count`, `holes`, and line/edge-based measures are compatible with Garcia, but not identical unless we implement that exact component taxonomy.

**From contour / glyph similarity papers**
These support the importance of:

- contour
- closed vs open shape
- filled / contour-only / data-lines-only distinctions
- shape similarity
- visual-channel distinguishability

So `contour count`, `filled-vs-outline proxy`, and perimeter/edge measures are conceptually supported, but they are pipeline adaptations.

**Not directly from the papers, but reasonable proxies**
These are engineering features I proposed because they are useful for icon comparison:

- bounding-box occupancy
- horizontal and vertical symmetry
- compression ratio as a complexity proxy
- filled-vs-outline proxy, unless treated only as an approximation of contour/fill style
- Canny edge density, if expressed as density rather than raw Canny edge count

So the clean wording should be:

> The feature set combines established paper-backed icon complexity metrics from Forsythe and Garcia with additional computational proxies for shape, symmetry, density, and style that support clustering and similarity analysis.

I would not claim all of them are “from the papers.”