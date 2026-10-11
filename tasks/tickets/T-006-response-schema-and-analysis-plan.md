# T-006: Define participant response schema and comparison analysis

Status: In progress (usability response schema implemented; final joins and analysis pending)
Priority: Medium  
Depends on: T-003, T-005

## Goal

Make human responses directly joinable to computer-derived icon and pair scores.

## Current progress (2026-09-29)

The usability D1 schema stores anonymous sessions and attempts with target/chosen IDs, assigned size, candidate order, selected position, input method, choice onset/response time, confidence, correctness, timing, interruption/repeated-exposure flags and optional debriefs. Protected CSV/JSON exports exist. These are usability records, not the final participant×icon/pair dataset or a completed human-computer join. The [pilot contract](../../wiki/icon-recognition-pilot.md) defines its exclusions; final statistical design and pair schemas remain provisional.

## Acceptance criteria

- Define one row per participant-stimulus response and one row per participant-pair response where needed.
- Include participant ID, trial ID, icon/pair IDs, chosen icon ID (or label only for a semantic task), correctness, confidence when applicable, similarity/confusability rating only for an approved pair task, response time if collected, and optional qualitative explanation.
- Define joins to per-icon family scores and pairwise family distances.
- Specify agreement, mismatch, correlation, and family-contribution analyses.
- Document missing-response and exclusion handling.
