# Thesis Evaluation Layers

These layers come from the local glyph/icon perception literature and the current thesis direction. They define how the computer-side visual feature families should be evaluated against human identification/perception.

## 1. Human Identification Layer

Purpose:

Measure what humans actually do when asked to identify or interpret a glyph/icon.

Human-side metrics:

- identification accuracy
- selected label or chosen meaning
- wrong-label/confusion choices
- confidence
- response time, if collected
- minimum identifiable size, if scale/zoom is tested

Use:

This is the main validation layer. Computer scores are not enough by themselves; the thesis needs human responses for comparison.

## 2. Perceived Similarity And Confusability Layer

Purpose:

Measure whether humans perceive two glyphs/icons as similar or easy to confuse.

Human-side metrics:

- pairwise similarity rating
- most-similar choice task
- perceived distinguishability rating
- confusion matrix from wrong identification responses

Use:

This layer connects directly to contour/similarity and quasi-Hamming-style distinguishability literature.

## 3. Computer Visual Feature Layer

Purpose:

Measure the visible properties of each icon using the active computer-vision feature families.

Active families:

- Complexity
- Shape/silhouette
- Stroke/structure
- Density/fill
- Balance/layout
- Color/contrast
- Texture

Computer-side metrics:

- per-feature normalized values
- per-family summary scores
- high/low examples per family
- feature reliability flags where needed

Use:

This layer is the computer-side measurement baseline. It should use active mapped features only, not excluded raw channels or semantic metadata.

## 4. Pairwise Distinguishability Layer

Purpose:

Measure whether two icons are visually far enough apart in computer feature space to be distinguishable.

Computer-side metrics:

- total visual distance
- family-wise distance
- nearest-neighbor rank
- distance margin to nearest competing icon
- quasi-Hamming-style count of different visual channels

Use:

Identification is set-relative. An icon may be visually clear alone but confusable if another icon is close in the active feature-family space.

## 5. Scale / Display Condition Layer

Purpose:

Measure whether identification survives zooming in/out or changing display size.

Human-side metrics:

- accuracy per rendered size
- confidence per rendered size
- minimum identifiable size
- confusion choices per rendered size

Computer-side metrics:

- nearest-neighbor scale stability
- scale confusability margin
- scale robustness AUC across tested sizes

Use:

Scale is an evaluation condition, not a new visual feature family.

Recommended sizes:

- 16 px
- 24 px
- 32 px
- 48 px
- 64 px
- 128 px
- 256 px

## 6. Human-Computer Agreement Layer

Purpose:

Compare human responses with computer-derived visual scores.

Analysis metrics:

- correlation between human scores and computer family scores
- regression or feature-importance analysis
- agreement cases where computer scores predict human behavior
- mismatch cases where humans identify differently from computer visual similarity
- family contribution to identification, similarity, and confusability

Use:

This is the final thesis comparison layer. It should answer which visual families explain human perception and where computer-based identification fails.

## Clean Evaluation Structure

```text
Active visual feature families
-> computer per-icon and pairwise scores
-> human identification/similarity/confusability scores
-> human-computer agreement and mismatch analysis
-> optional scale robustness condition
```

## Boundary

Do not evaluate semantic meaning, familiarity, metaphor, historical knowledge, or cultural convention as computer-vision features.

These can be used only as:

- metadata/context
- study prompts
- human-study outcomes
- control variables
