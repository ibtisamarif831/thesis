# Icon/Glyph Perception Thesis Workspace

This repository contains the datasets, literature, computer-vision pipeline, similarity analysis, dashboard, and planned human-evaluation layer for a thesis comparing literature-derived visual feature families with human icon/glyph identification and perception.

Start with the **[repository wiki](wiki/README.md)**. It covers the thesis boundary, all 13 datasets, the end-to-end pipeline, feature extraction, active visual families, similarity/clustering, dashboard UI and implementation, literature, evaluation plan, commands, artifacts, verification, and agent workflows.

For AI-agent rules, read [AGENTS.md](AGENTS.md) first, followed by the detailed routing guide in [agent.md](agent.md).

## Run the Dashboard

From the repository root:

```powershell
python -m http.server 8765 --bind 127.0.0.1
```

Open:

```text
http://127.0.0.1:8765/icon_data/analysis/analysis_dashboard/index.html
```

The current dashboard is a computer-side diagnostic interface. It does not yet contain participant-response results or a completed human-computer comparison.
