# Limitations and Backlog

[Wiki home](README.md) · [Evaluation](evaluation-and-human-study.md) · [Dashboard implementation](dashboard-implementation.md)

## Thesis-Level Gaps

- No finalized human-study stimulus subset.
- An implemented usability-task protocol exists; final research task/conditions, exposure controls and approval remain unfinished.
- The [recognition usability pilot](icon-recognition-pilot.md) has anonymous response storage and a task-design workflow; final-study response schemas and analysis remain unfinished.
- No collected human identification/perception scores.
- No joined human-computer statistical analysis.
- No implemented quasi-Hamming-style channel-difference explanation.

These are essential to the thesis objective. The existing computer pipeline and dashboard do not substitute for them.

Received nominations are not a consensus set. The `ibtisam` entry is algorithm-assisted and must not be counted as an independent human rater. The recognition prototype shows a large target before smaller candidates, creating exposure/memory effects; the new controlled version assigns candidate sizes but does not yet provide calibrated physical thresholds or an approved final-study analysis. See [meeting decisions](meeting-decisions-and-status.md).

## Data and Metadata Gaps

- OCHA source categories/tags are richer than the unified CSV currently exposes.
- Mulberry grammar, categories, multilingual labels, and tags are only partly propagated.
- USP canonical rows use numeric labels; human-readable medication instructions need structured extraction.
- AIGA categories can be further normalized from Wikimedia/local titles.
- ISO 7010 rows primarily retain code IDs rather than human-readable meanings.
- Public ISO-related repositories are implementations, not official ISO distributions.
- McDougall standalone original stimuli remain request-only; local stimuli are appendix extractions.

## Feature-System Limitations

- Schema-v2 engineering measurements are implemented, but the frozen two-rater benchmark is not yet rated; the all-family feature-validation pilot release gate therefore remains blocked. The separate task-design pilot does not satisfy or change it.
- Opaque full-scene or nonuniform-background masks are explicitly flagged uncertain and require overlay review rather than automatic acceptance.

- Active metrics are proxies, not direct measurements of human perception.
- Connected-component/contour groupings can differ from human grouping.
- Enclosure, arrowhead, and arc metrics remain computational approximations.
- Texture has one active schema-v2 local-variation channel pending human validation.
- Raw Hu, LBP, text/letter, and crush-stability channels remain excluded from active claims.
- Full-corpus feature extraction is complete, but low/high examples still require systematic human visual validation per family.

## Similarity and Clustering Limitations

- Distance depends on preprocessing, feature weights, family weights, and comparison-set composition.
- PCA is a lossy 2D projection.
- Cluster labels are descriptive and arbitrary.
- Hierarchical clustering lacks a dendrogram.
- No human confusability data validates the current nearest-neighbor rankings.
- Browser image-view clusters after interactive changes are not exported.

## Dashboard Limitations

- Image and AI Clustering use the seven-family stratified composite, up to 20 unique icons per family and up to 140 for All; sparse bins or color cohorts can produce fewer. Metadata/Combined remain limited to the generated 50-row sample.
- Dashboard correlation data and Feature Values use all 649 rows from the five retained source sets, not the complete 28,749-row corpus. Feature Groups excludes 252 uncertain-mask rows, then divides each eligible family/cohort feature range into 10 equal-width bins and randomly draws up to two icons per bin from the remaining 397-row compact pool. Empty or undersized bins are not backfilled, so individual family samples can contain fewer than 20 icons. It supports three-icon representative comparisons; Image and AI Clustering combine all seven family samples and exclude cross-family duplicates.
- Color By is present but not applied to the visible icon overlays.
- Current filtering is by icon set only; category/style filters described in older docs are absent.
- UI state is not shareable by URL and resets on reload.
- The app is generated as a large inline HTML/CSS/JS string inside a large Python script.
- Private recognition-pilot summaries/exports exist; a final-study participant analysis or human-computer comparison view remains unfinished.

## Engineering Limitations

- AI Clustering is local-only and depends on OpenRouter availability, provider pricing, and user-supplied credits.
- Its label-independent metrics describe agreement with feature clustering, not correctness, semantic quality, or superiority.
- The deliberately tracked SQLite cache/history is a single-writer artifact and can create binary merge conflicts across branches.

- Several large scripts combine multiple responsibilities.
- Dense pairwise similarity and hierarchical clustering are quadratic and are not safe to run over all 28,749 icons without a scalable redesign.
- Dependency availability varies by local runtime.
- An earlier Windows runtime check lacked `pdfplumber`; this is historical environment evidence, not a check of the current macOS runtime.
- Static visualizations degrade to summary-only when Matplotlib is missing.
- Some generated/output documentation contains older macOS-specific runtime paths.

## Prioritized Backlog

The active implementation sequence is maintained in `tasks/tickets/`. The current color filter brief and the initial one-feature-per-family selection are implemented; the older five-cohort pixel-classification criteria and candidate review remain open:

1. Foreground-color cohorts in Feature Groups — current All/B/W/Red/Colored UI implemented; original ticket's separate black/white and ambiguity handling remain.
2. Representative family-feature selection — done; browse and document candidate stimuli next.
3. Per-icon family score and pairwise family-distance exports.
4. Controlled groups and matched pairs.
5. Review the implemented recognition usability prototype and conduct the approved human pilot; decide whether a separate similarity/discrimination task is needed.
6. Complete final-study schemas, computer-score joins and comparison analysis; usability storage/exports are already implemented.

Supporting work should include:

- fix or remove nonfunctional Color By UI;
- keep the dashboard README and wiki aligned with current controls;
- add category/style filters only if still useful and specified;
- add a dendrogram if hierarchical structure needs explanation;
- continue the staged [review, feature pipeline, and dashboard refactoring plan](../tasks/review-feature-dashboard-refactoring-plan.md); the characterized shared registry slice is complete, while explicit populations/profiles, pure services, modular browser state/UI, and transactional orchestration remain;
- add end-to-end browser regression checks;
- enrich high-priority metadata sources;
- visually audit feature examples before study selection.

## How to Update This Page

Remove a limitation only after authoritative evidence proves it is resolved. Link the implementing ticket or script, generated artifact, and verification result. Move newly discovered durable gaps here instead of hiding them in transient task narration.
