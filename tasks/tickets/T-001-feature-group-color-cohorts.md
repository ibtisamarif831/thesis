# T-001: Add color-cohort filters to Feature Groups

Status: Todo  
Priority: High  
Depends on: none

Linear: PER-6

## Goal

Split Feature Groups examples into `All`, `Black`, `White`, `Red`, and `Other colored` cohorts, as requested in the meeting notes.

## Acceptance criteria

- The Feature Groups view exposes the five cohort filters.
- Each filter updates the visible icon examples and counts.
- The cohort is based on foreground pixels, not only `is_monochrome`.
- Black and white monochrome icons are distinguishable; red is identified by hue; ambiguous cases are reported rather than silently forced.
- A small sample of each cohort is visually checked.
