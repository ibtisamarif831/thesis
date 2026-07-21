# Glossary

[Wiki home](README.md) · [Thesis overview](thesis-overview.md)

| Term | Meaning in this repository |
|---|---|
| Active feature | One of 81 image-derived numeric columns included in the current literature-mapped thesis analysis. |
| Active visual family | One of seven interpretable groups: Complexity, Shape/silhouette, Stroke/structure, Density/fill, Balance/layout, Color/contrast, Texture. |
| Canonical icon | The one selected representation of a source stimulus that is allowed into `dataset.csv` after dataset-specific duplicate/helper filtering. |
| Canonical dataset | `icon_data/analysis/dataset.csv`, the cross-source table of canonical icon rows. |
| Cluster | An algorithmic group in a selected standardized feature space; not a semantic class. |
| Combined variant | Dashboard matrix containing image and encoded metadata features; exploratory, not a pure visual space. |
| Computer-side score | An image feature, family summary, or pairwise distance computed from active visual measurements. |
| Confusability | Risk that two stimuli are mistaken for one another; currently predicted by visual distance and awaiting human validation. |
| Dashboard sample | Current 129-row random per-set sample used by the Clustering view. |
| Distinguishability | Visual separation between icons, especially relative to competing icons in a set. |
| Excluded raw channel | Numeric extractor output retained in `features.csv` but barred from active thesis analysis under the current mapping. |
| Feature extractor | Registered code component that computes one or more numeric columns from a normalized image. |
| Feature corpus | Complete 28,749-row `features.csv` population covering every canonical icon. |
| Feature Review | Dashboard view using Spearman correlation, variance, and missingness to inspect redundancy among active features. |
| Feature Values | Dashboard view showing low, mean-nearest, and high examples for up to two low-redundancy features per family. |
| Glyph/icon | A compact visual symbol used as a study stimulus. The project uses both terms because the literature and datasets span iconography, pictograms, signs, emoji, and data glyphs. |
| Human-side score | Participant outcome such as identification accuracy, confidence, similarity, confusability, or response time. Not implemented yet. |
| Metadata feature | Encoded source/category/style/token/rating context used in exploratory dashboard variants; not an image-derived visual family. |
| Normalized image | Generated 256 × 256 centered PNG representation used as the common extraction input. |
| PCA | Principal component analysis used to project a selected high-dimensional feature matrix into two display dimensions. |
| Proxy | A computable measurement that approximates, but does not directly equal, a human perceptual construct. |
| Quasi-Hamming framing | Distinguishability idea based on how many visual channels differ; a future explainability layer, not yet implemented. |
| Raw feature | Any of the 100 numeric image columns written by the extractor, including active and excluded channels. |
| Semantic identity | What an icon means or depicts. Stored/assessed through metadata or people, not claimed as an active pixel-derived family. |
| Spearman rho | Rank correlation used by Feature Review to assess monotonic redundancy between feature columns. |
| Stable ID | `icon_id`, a 16-character SHA-1 prefix derived from the canonical source path. Stable only while that path remains unchanged. |
