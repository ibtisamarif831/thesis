# Limitations and Backlog

[Wiki home](README.md) · [Evaluation](evaluation-and-human-study.md) · [Dashboard implementation](dashboard-implementation.md)

## Thesis-Level Gaps

- No finalized human-study stimulus subset.
- No complete participant protocol.
- No implemented response schemas or collection workflow.
- No collected human identification/perception scores.
- No joined human-computer statistical analysis.
- No implemented quasi-Hamming-style channel-difference explanation.

These are essential to the thesis objective. The existing computer pipeline and dashboard do not substitute for them.

## Data and Metadata Gaps

- OCHA source categories/tags are richer than the unified CSV currently exposes.
- Mulberry grammar, categories, multilingual labels, and tags are only partly propagated.
- USP canonical rows use numeric labels; human-readable medication instructions need structured extraction.
- AIGA categories can be further normalized from Wikimedia/local titles.
- ISO 7010 rows primarily retain code IDs rather than human-readable meanings.
- Public ISO-related repositories are implementations, not official ISO distributions.
- McDougall standalone original stimuli remain request-only; local stimuli are appendix extractions.

## Feature-System Limitations

- Schema-v2 engineering measurements are implemented, but the frozen two-rater benchmark is not yet rated; the all-family pilot release gate therefore remains blocked.
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

- Clustering sample is 129 rows, not the full dataset or full feature sample.
- Feature Review/Values use the complete 28,749-row corpus. Feature Groups draws random 20-icon family samples from a compact full-corpus pool, while clustering remains limited to 129 rows.
- Color By is present but not applied to the visible icon overlays.
- Current filtering is by icon set only; category/style filters described in older docs are absent.
- UI state is not shareable by URL and resets on reload.
- The app is generated as a large inline HTML/CSS/JS string inside a large Python script.
- No participant-response or human-computer comparison view exists.

## Engineering Limitations

- Several large scripts combine multiple responsibilities.
- Dense pairwise similarity and hierarchical clustering are quadratic and are not safe to run over all 28,749 icons without a scalable redesign.
- Dependency availability varies by local runtime.
- `extract_paper_text.py` currently fails under the verified Windows Python because `pdfplumber` is absent.
- Static visualizations degrade to summary-only when Matplotlib is missing.
- Some generated/output documentation contains older macOS-specific runtime paths.

## Prioritized Backlog

The active implementation sequence is maintained in `tasks/tickets/`. The current color filter brief and the initial one-feature-per-family selection are implemented; the older five-cohort pixel-classification criteria and candidate review remain open:

1. Foreground-color cohorts in Feature Groups — current All/B/W/Red/Colored UI implemented; original ticket's separate black/white and ambiguity handling remain.
2. Representative family-feature selection — done; browse and document candidate stimuli next.
3. Per-icon family score and pairwise family-distance exports.
4. Controlled groups and matched pairs.
5. Pilot human identification/similarity study.
6. Response schemas and comparison analysis.

Supporting work should include:

- fix or remove nonfunctional Color By UI;
- reconcile dashboard README with current controls;
- add category/style filters only if still useful and specified;
- add a dendrogram if hierarchical structure needs explanation;
- extract dashboard templates/logic into maintainable modules;
- add end-to-end browser regression checks;
- enrich high-priority metadata sources;
- visually audit feature examples before study selection.

## How to Update This Page

Remove a limitation only after authoritative evidence proves it is resolved. Link the implementing ticket or script, generated artifact, and verification result. Move newly discovered durable gaps here instead of hiding them in transient task narration.
