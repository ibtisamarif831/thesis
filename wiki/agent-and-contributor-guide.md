# Agent and Contributor Guide

[Wiki home](README.md) · [Repository architecture](repository-architecture.md) · [Verification](verification-and-troubleshooting.md)

## First Five Minutes

1. Read `agent.md` for durable repository rules and current routing.
2. Read this wiki home and the page relevant to the task.
3. Check `git status --short`; existing changes belong to the user unless proven otherwise.
4. Inspect the current generator and artifact before relying on prose documentation.
5. State the research boundary whenever a change touches features, similarity, dashboard interpretation, or thesis claims.

## Query Routing

| Task | Start with |
|---|---|
| Dataset membership or count | [Datasets and provenance](datasets-and-provenance.md), then `dataset.csv` and `build_icon_dataset.py` |
| Feature definition or extraction | [Feature system](feature-system.md), then `features_metadata.json` and extractor code |
| Similarity math | [Similarity and clustering](similarity-and-clustering.md), then `similarity_metadata.json` and script |
| Dashboard behavior | [Dashboard UI](dashboard-ui.md), then generated page and generator |
| Dashboard schema/change | [Dashboard implementation](dashboard-implementation.md) |
| Human-study work | [Evaluation and human study](evaluation-and-human-study.md), then the matching ticket |
| Thesis claim/literature support | [Literature and evidence](literature-and-evidence.md), then original PDF |
| Running/regeneration | [Commands and scripts](commands-and-scripts.md) |

## Working Rules

- Search with `rg` before broad inspection.
- Preserve unrelated working-tree changes.
- Change generators before generated outputs.
- Keep active visual features separate from semantic metadata.
- Use deterministic sampling and record seeds.
- Do not silently change source collection versions, licenses, or canonical identity rules.
- Keep new substantive Python logic in importable modules with thin CLI wrappers.
- Add focused tests for reusable non-trivial behavior.
- Verify through the real output surface: CSV/JSON plus rendered HTML when UI is involved.
- Update documentation when a behavior, command, schema, known gap, or current-state fact changes.

## Evidence Standard

Use direct evidence for claims:

- behavior: current executable code and runtime result;
- row/schema state: current generated CSV/JSON;
- UI state: served browser page and console/network checks;
- literature claim: original PDF and page;
- project priority: current status file/ticket.

Prose summaries are routing aids. If a README says category/style filters exist but the current generated HTML exposes only set filters, document and follow the implementation until the discrepancy is intentionally resolved.

## Feature and Thesis Guardrails

Before adding an active feature, answer:

1. Is it visible in the image?
2. Can it be computed consistently from normalized pixels?
3. Does local literature support the perceptual construct?
4. Is the implemented metric an honest proxy with clear limitations?
5. Can low/high examples be visually validated?
6. Does it avoid encoding labels or source identity as visual evidence?

Semantic labels, exact text identity, familiarity, meaningfulness, metaphor, history, and cultural convention belong in metadata or the human study.

## Generated-Artifact Discipline

For a dashboard change:

1. edit `code/build_analysis_dashboard.py` or a shared module;
2. run syntax/tests;
3. regenerate `icon_data/analysis/analysis_dashboard/`;
4. inspect output counts/schema;
5. serve and test the UI;
6. update the dashboard wiki pages if needed.

Apply the same producer-first rule to dataset, feature, similarity, and literature outputs.

## Handling Existing Documentation

The repository contains older notes and status snapshots. Do not delete them merely because the wiki consolidates their information. Instead:

- keep authoritative files current;
- link them to the wiki;
- call out stale or historical material;
- avoid duplicating volatile counts across many pages;
- update the wiki snapshot only after verifying artifacts.

## Before Closing a Task

- Review the actual user objective and all acceptance criteria.
- Run proportionate tests and artifact checks.
- Inspect `git diff` for accidental or unrelated changes.
- Apply the mandatory wiki completion gate from `AGENTS.md`; repository-changing work is not complete while its documentation is stale.
- Review `agent.md` and add only durable new guidance that helps the next agent.
- Update every affected wiki page when durable knowledge changed, verify its links/facts, and name the updated pages in the final handoff.
- Report what changed, what was verified, and any remaining limitations.

Do not claim the full thesis pipeline is complete until participant collection and human-computer analysis exist and are verified.
