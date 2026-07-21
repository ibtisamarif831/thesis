# Repository Instructions for AI Agents

These instructions apply to every AI agent working anywhere in this repository.

## Required Orientation

Before making changes:

1. Read `agent.md` for repository routing, current state, and working rules.
2. Read `wiki/README.md` and the wiki page relevant to the task.
3. Inspect the current authoritative code, artifact, or status file before relying on documentation.

## Mandatory Wiki Completion Gate

A repository-changing task is not complete until the wiki has been reviewed and brought into alignment with the work.

Before declaring a task complete, every agent must:

1. Identify which wiki pages describe the subsystem that changed.
2. Update those pages in the same task whenever the work changes behavior, UI, pipeline steps, schemas, datasets, feature definitions, commands, dependencies, outputs, verification procedures, project status, limitations, or backlog state.
3. Update the dated snapshot in `wiki/README.md` only after verifying changed counts or state from authoritative artifacts.
4. Add a focused new wiki page and link it from `wiki/README.md` if no existing page can clearly hold the new durable knowledge.
5. Check affected wiki links and review the final diff for stale or contradictory claims.
6. State in the final handoff which wiki pages were updated.

Do not add filler edits merely to touch the wiki. For a read-only question or a task that produces no durable repository or operational change, review the relevant wiki page but leave it unchanged if it remains accurate. For every code, data, UI, pipeline, configuration, or workflow change, a wiki edit is required unless the agent can demonstrate that the existing documentation already describes the resulting state exactly.

## Documentation Authority

The wiki organizes knowledge but does not override executable evidence. Use this order when resolving conflicts:

1. Current executable code and runtime behavior.
2. Current generated CSV/JSON reports and rendered artifacts.
3. Current status files and task acceptance criteria.
4. Wiki explanations and routing.
5. Older notes and historical plans.

When a conflict is found, fix the implementation or documentation as appropriate during the task; do not knowingly leave the wiki stale.

## Preserve User Work

Check `git status --short` before editing. Existing or unrelated changes belong to the user. Do not revert, delete, or overwrite them unless explicitly requested.

