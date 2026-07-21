# Wiki Maintenance

[Wiki home](README.md) · [Agent guide](agent-and-contributor-guide.md)

## Purpose

The wiki organizes durable repository knowledge for humans and AI agents. It should make the system navigable without becoming a second, conflicting implementation specification.

## Mandatory Completion Gate

`AGENTS.md` requires every agent to review the relevant wiki pages before completing a task. When repository behavior or operational knowledge changes, updating the wiki is part of the implementation—not an optional follow-up.

Before handing work back, the agent must:

1. identify every affected wiki page;
2. update behavior, schemas, commands, counts, limitations, status, and verification guidance as applicable;
3. add and index a focused page when the subject has no suitable home;
4. verify affected local links and facts against current code/artifacts;
5. name the updated wiki pages in the final response.

Read-only work does not require a meaningless documentation edit. It does require checking the relevant page and correcting it if the investigation reveals that it is stale.

## Documentation Layers

| Layer | Role |
|---|---|
| Wiki | Organized explanations, workflows, navigation, caveats. |
| `agent.md` | Compact first-stop routing and agent rules. |
| Status/tickets | Current direction, completion state, acceptance criteria. |
| Dataset/analysis READMEs | Local artifact instructions and dataset-specific notes. |
| Generated metadata | Exact state of a completed run. |
| Code | Executable behavior and schema generation. |

Keep each fact at the most appropriate layer and link rather than copy large volatile structures.

## Page Conventions

- Use lowercase kebab-case filenames.
- Begin with a clear title and links back to the wiki home and adjacent topics.
- Mark planned behavior explicitly.
- Include commands from the repository root.
- Use repository-relative paths in prose/code.
- Date only volatile snapshots, not durable explanations.
- State the authoritative script/artifact for every subsystem.
- Distinguish observed current behavior from intended behavior.

## When to Update

Update the relevant page when any of these change:

- research boundary or evaluation design;
- dataset source, canonical count, selection rule, or schema;
- normalization or feature computation;
- active family membership or interpretation;
- similarity preprocessing or weights;
- dashboard views, controls, runtime state, or JSON contract;
- commands, dependencies, output locations, or verification procedures;
- a known limitation or ticket status.

If a code or data change affects none of these items, explicitly verify that the existing page already describes the resulting state before completing the task.

## Current Snapshot Procedure

Before changing numbers on `wiki/README.md`:

1. read the current CSV/JSON artifacts;
2. check that failure reports belong to the latest relevant run;
3. confirm the generating code/configuration;
4. update the verification date;
5. update dependent pages only where the same count is necessary.

## Link and Consistency Review

Check:

- every page is linked from `wiki/README.md`;
- every relative Markdown target exists;
- no page calls metadata a visual family;
- current and planned features are clearly separated;
- the two dashboard sample populations are not conflated;
- dashboard controls match generated HTML;
- older README claims are either corrected or explicitly called out;
- macOS-specific historical runtime paths are not presented as portable commands.

## Avoiding Documentation Drift

- Prefer a table generated from/read against metadata over a manually repeated count.
- Keep complete machine-readable registries in generated JSON, with the wiki explaining how to interpret them.
- Add schema/version metadata when new downstream consumers appear.
- Treat UI verification as required evidence for UI documentation.
- Add a concise durable note to `agent.md` after discovering an important routing rule or pitfall.

## Adding a Page

1. Confirm the topic is durable and does not belong only in a ticket.
2. Choose a focused title and file.
3. Link authoritative sources and adjacent wiki pages.
4. Add the page to the home navigation.
5. Run link and consistency checks.
6. Avoid duplicating a whole source README when a summary and link are enough.
