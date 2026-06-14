# Thesis Orientation

This thesis workspace appears to be about glyph and icon design for information visualization, with a focus on how visual complexity, abstractness, contour, and perceptual discriminability affect how people interpret small visual symbols.

## Working Thesis Topic

The likely thesis area is:

> How to design, evaluate, and possibly automate the selection of effective glyphs/icons for multivariate data visualization by accounting for perceptual similarity, visual complexity, abstractness, and error-resistant distinguishability.

The papers in `papers/` point to a thesis at the intersection of:

- Data glyph visualization for multidimensional or multivariate data.
- Human perception of glyph similarity, especially star glyphs and contour effects.
- Icon/glyph complexity and abstractness as measurable design variables.
- Systematic glyph design methods, including taxonomies and information-theoretic distance.
- Evaluation methods for glyph design through empirical studies or automated metrics.

## Core Paper Themes

| Paper | Role in Thesis |
|---|---|
| `Glyph-based_Visualization_Foundations_Design_Guidelines_Techniques_Applications.pdf` | Broad foundation paper. Defines glyph-based visualization, design guidelines, visual channels, semiotics, applications, and limitations. Use this for literature review framing. |
| `A_Systematic_Review_of_Experimental_Studies_on_Data_Glyphs.pdf` | Empirical landscape. Reviews 64 user-study papers on data glyphs, including glyph types, tasks, study designs, and open research directions. Use this to justify the research gap and evaluation method. |
| `The_Influence_of_Contour_on_Similarity_Perception_of_Star_Glyphs.pdf` | Perceptual study model. Tests whether contours improve similarity judgments in star glyphs; finds simple star glyphs without contours often perform best. Useful as a template for an experiment. |
| `Forsythe-Measuring_cion_complexity_automated.pdf` | Automated icon complexity measurement. Shows image-processing features such as perimeter, edge detection, and quadtree structural variability can estimate perceived complexity. Useful for computational metrics. |
| `Garcia-Development_validation_icons_abstractness.pdf` | Icon abstractness/concreteness. Proposes a quantitative metric for abstractness and validates it against subjective judgments; shows concrete icons are generally identified better than abstract icons and context matters. |
| `Glyph_Visualization_A_Fail-Safe_Design_Scheme_Based_on_Quasi-Hamming_Distances.pdf` | Distinguishability and fail-safe glyph design. Uses quasi-Hamming distance to reason about glyph sets that remain distinguishable under perceptual or display errors. Useful for optimization/design criteria. |
| `Taxonomy-Based_Glyph_Designwith_a_Case_Study_on_Visualizing_Workflows_of_Biological_Experiments.pdf` | Systematic glyph construction. Proposes taxonomy-driven glyph design by mapping concept hierarchies to visual-channel discriminability, demonstrated on biological experiment workflows. |

## Likely Research Problem

Glyphs are compact and useful for encoding multidimensional information, but they are hard to design well because:

- Small glyphs can become visually ambiguous.
- Similar glyphs can be confused under noise, scale reduction, poor display, or print artifacts.
- More complex icons may be harder to recognize or search for.
- Abstract icons/glyphs may be harder to match to meaning than concrete ones.
- Design often relies on designer intuition rather than repeatable metrics.

The thesis can contribute by connecting empirical HCI/visualization evidence with measurable glyph properties.

## Plausible Research Questions

Good candidate research questions based on the paper set:

1. Can automated visual complexity metrics predict perceived difficulty, similarity judgments, or search performance for glyph/icon sets?
2. How do contour, shape closure, or reference marks affect similarity detection in star glyphs or custom glyphs?
3. Can a taxonomy-based or quasi-Hamming-distance design process produce glyph sets that are more distinguishable than intuition-based designs?
4. What tradeoff exists between semantic meaningfulness, abstractness/concreteness, and perceptual discriminability in icon/glyph design?

## Recommended Narrow Thesis Direction

The fastest coherent thesis direction would be:

> Build or evaluate a small glyph/icon design pipeline that computes visual complexity and discriminability metrics, then test whether those metrics align with human similarity or identification performance.

A concrete version:

> Compare a set of glyphs/icons across automated complexity metrics, quasi-Hamming-style distance measures, and a small user task measuring similarity judgments or recognition accuracy.

This direction uses all major paper themes without becoming too broad.

Dataset priority: this thesis will use scientific icon/pictogram sets first. Primary stimuli should come from sets that were used, normed, or evaluated in scientific research, preferably across different domains such as HCI symbols, transportation signs, AAC pictograms, safety/hazard pictograms, healthcare wayfinding, medication instructions, and medical-device labeling. General-purpose icon libraries should only be used as secondary comparison material when they have weak, indirect, or no research-use evidence.

## Suggested Thesis Structure

1. Introduction
   - Problem: glyphs/icons are powerful but can fail when too complex, abstract, or visually similar.
   - Motivation: empirical visualization and HCI need repeatable design/evaluation methods.

2. Literature Review
   - Glyph-based visualization foundations and design guidelines.
   - Experimental studies of data glyphs.
   - Star glyph similarity and contour effects.
   - Icon complexity and abstractness metrics.
   - Fail-safe glyph design and quasi-Hamming distance.
   - Taxonomy-based glyph design.

3. Methodology
   - Define glyph/icon dataset or stimulus set, prioritizing scientific research-used sets before general-purpose icon libraries.
   - Compute visual features: complexity, edge/perimeter measures, visual-channel encodings, pairwise distinguishability.
   - Optional user study: similarity judgment, recognition, search, or matching task.

4. Results
   - Report metric distributions and correlations.
   - Compare human performance across glyph/icon conditions.
   - Identify which design features help or harm recognition/similarity judgments.

5. Discussion
   - Interpret the tradeoff between complexity, abstractness, semantic meaning, and discriminability.
   - Translate findings into design recommendations.

6. Conclusion
   - Summarize contribution: a measured, evidence-based approach to glyph/icon design.

## Current Workspace Evidence

- `papers/` contains seven core PDFs on glyph visualization, icon complexity, abstractness, contour perception, taxonomy-based design, and fail-safe glyph distinguishability.
- `THESIS_CHECKLIST.md` already frames the thesis as lying at the intersection of data glyphs, visual/icon complexity, and perception/design guidelines.
- `icon_data/` contains downloaded/extracted standardized icon, picture, food, and 3D-object stimulus sets that could support empirical or metric-based analysis.
- `source.md` documents the stimulus source links and download status.

## Notes for Future Agents

- Treat `papers/` as the thesis literature backbone.
- Use `icon_data/iconsets/` as the current organized stimulus dataset area.
- Do not assume the thesis is about generic icons only; the stronger framing is glyph/icon design for empirical visualization and HCI.
- If building software, a focused metric pipeline is more aligned with the paper set than a broad visualization application.
- If designing a study, star glyph similarity or icon recognition/search tasks are the best-supported experimental models.
