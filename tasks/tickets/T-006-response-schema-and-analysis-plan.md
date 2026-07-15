# T-006: Define participant response schema and comparison analysis

Status: Todo  
Priority: Medium  
Depends on: T-003, T-005

## Goal

Make human responses directly joinable to computer-derived icon and pair scores.

## Acceptance criteria

- Define one row per participant-stimulus response and one row per participant-pair response where needed.
- Include participant ID, trial ID, icon/pair IDs, chosen label, correctness, confidence, similarity/confusability rating, response time if collected, and qualitative explanation.
- Define joins to per-icon family scores and pairwise family distances.
- Specify agreement, mismatch, correlation, and family-contribution analyses.
- Document missing-response and exclusion handling.
