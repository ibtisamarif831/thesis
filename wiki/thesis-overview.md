# Thesis Overview

[Wiki home](README.md) · [Literature](literature-and-evidence.md) · [Evaluation](evaluation-and-human-study.md)

## Thesis Title and Direction

**Title:** Perception of Glyphs

The supervisor-defined objective is to develop and run user studies that determine when a set of glyphs remains discernible as its display size is reduced. Size reduction is therefore the primary experimental condition, not an optional extension.

The computational work supports that objective by organizing literature-grounded visual properties into measurable feature families. Those measurements help select controlled glyph sets and explain why particular glyphs remain distinguishable or become confused at smaller sizes.

The intended comparison has two sides:

1. **Computer side:** values derived from visible pixels, summarized through literature-mapped visual families and pairwise distances to support stimulus selection and interpretation.
2. **Human side:** identification and discrimination across decreasing pixel sizes, with accuracy, confusion, confidence, and response time as candidate outcomes.

The final analysis should estimate the smallest size at which each glyph set remains reliably discernible, then explain which visible families predict that threshold, where they do not, and what non-visual factors may explain the remaining difference.

## What This Repository Is

This is an empirical and computational thesis workspace. It contains:

- 13 icon/glyph datasets and their provenance;
- a canonical cross-dataset table and normalized images;
- image-feature extraction;
- literature-mapped active visual families;
- similarity, clustering, feature-review, and dashboard tooling;
- literature PDFs, extracted text, and mapping notes;
- a planned evaluation and human-study layer.

It is not primarily a generic icon library, semantic image-understanding system, or clustering demonstration.

## Allowed Computer-Side Claims

The current implementation can support claims about:

- measurable visual structure in normalized icon images;
- interpretable feature families grounded in local literature;
- computer-side similarity, distance, and potential confusability;
- how features and feature families vary across selected stimuli;
- agreement or mismatch with human scores once those scores exist.

The current implementation does **not** prove that the computer understands icon meaning or models perception completely.

## Visual and Non-Visual Boundary

| Visible and computable from pixels | Not a computer-vision family |
|---|---|
| Edge/detail load | Familiarity |
| Shape and silhouette | Meaningfulness |
| Stroke direction and graph structure | Semantic identity |
| Fill, density, and stroke width | Metaphor |
| Symmetry and spatial layout | Cultural or historical convention |
| Color, hue, and contrast | Learnability |
| Tonal texture | Context-dependent interpretation |

Non-visual factors may still be scientifically important. Store them as metadata, collect them from participants, or use them as control variables; do not present them as image-derived feature evidence.

## Analysis Layers

```mermaid
flowchart TD
    A["Controlled glyph sets"] --> B["Decreasing pixel-size conditions"]
    B --> C["Human identification and discrimination"]
    D["Per-icon computer measurements"] --> E["Feature-based hypotheses"]
    F["Pairwise visual distances"] --> E
    C --> G["Discernibility thresholds"]
    E --> H["Agreement and mismatch analysis"]
    G --> H
```

The planned layers are:

- fixed display-size conditions;
- human identification and pairwise discrimination;
- confusion, confidence, and response time;
- computer visual features;
- pairwise distinguishability;
- per-set or pairwise discernibility thresholds;
- human-computer agreement and mismatch.

See [Evaluation and human study](evaluation-and-human-study.md) for proposed measures and tables.

## Current State

Completed work includes dataset assembly, full-corpus normalization and feature extraction, active-family correction, similarity preprocessing on the earlier pilot, dashboard feature views, literature extraction, and evaluation-layer documentation.

The main missing thesis layer is the size-controlled human study and the statistical join between participant responses and computer-side scores. The size conditions, final stimulus sets, study protocol, response schema, and threshold-analysis scripts remain in the active backlog.

Authoritative status files:

- `THESIS_STATUS.md`
- `tasks/current-thesis-next-steps.md`
- `tasks/tickets/README.md`
- `code/evaluation/evaluation_layers.md`
