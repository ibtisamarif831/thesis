# T-003: Export computer-side family scores for study stimuli

Status: Todo  
Priority: High  
Depends on: T-002  
Linear: PER-7

## Goal

Produce machine-readable scores that can be joined to the eventual human-study responses.

## Acceptance criteria

- Export one row per icon with active family summaries for Complexity, Shape/silhouette, Stroke/structure, Density/fill, Balance/layout, Color/contrast, and Texture.
- Keep raw feature columns separate from family summaries.
- Export pairwise total and family-wise distances for selected icon pairs.
- Include stable `icon_id` values and source paths.
- Document normalization/aggregation choices.
