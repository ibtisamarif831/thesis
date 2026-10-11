# Icon/Glyph Perception Thesis Workspace

This repository contains the datasets, literature, computer-vision pipeline, similarity analysis, dashboard, internal stimulus nominations, recognition usability prototype, and planned final human-evaluation layer for a thesis comparing literature-derived visual feature families with human icon/glyph identification and perception.

Start with the **[repository wiki](wiki/README.md)**. It covers the thesis boundary, all 13 datasets, the end-to-end pipeline, feature extraction, active visual families, similarity/clustering, dashboard UI and implementation, literature, evaluation plan, commands, artifacts, verification, and agent workflows.

For AI-agent rules, read [AGENTS.md](AGENTS.md) first, followed by the detailed routing guide in [agent.md](agent.md).

The separate LaTeX/Overleaf project and its current source and Git state are documented in [the thesis document handoff](THESIS_DOCUMENT_HANDOFF.md).

The repository-local thesis-writing skill is at [.codex/skills/thesis-writing/SKILL.md](.codex/skills/thesis-writing/SKILL.md).

Current progress and meeting decisions: [Thesis status](THESIS_STATUS.md), [current tasks](tasks/current-thesis-next-steps.md), and [meeting evidence](wiki/meeting-decisions-and-status.md). The full meeting transcript is preserved under `notes/meetings/`.

## Run the Dashboard

From the repository root:

```bash
.venv/bin/python code/serve_analysis_dashboard.py --port 8765
```

Open:

```text
http://127.0.0.1:8765/
```

The local dashboard is a computer-side diagnostic interface; its API server supports local AI execution. The [public edition](https://glyph-perception-dashboard.pages.dev/) has separate reviewer nominations and a private recognition usability workflow. Neither synthetic pilot checks nor nominations are research participant evidence, and no human-computer comparison has been completed.
