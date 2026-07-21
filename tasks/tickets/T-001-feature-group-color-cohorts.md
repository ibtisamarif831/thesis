# T-001: Add color-cohort filters to Feature Groups

Status: In progress (strict Red implemented; separate Black/White cohorts still open)
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

## Current progress

Feature Groups provides All, B/W, Red, and Colored filters with live counts. Red now uses only `strict_red_flag_v2`, requiring at least 90% corrected foreground pixels in the strict HSV red range; dataset names and labels are not used. Separate Black and White cohorts and broader ambiguity reporting remain open, so this ticket stays in progress.
