# T-005: Design a pilot human glyph-identification study

Status: In progress (usability prototype implemented; final research protocol pending)
Priority: High  
Depends on: T-004

## Goal

Agree one primary size-dependent human outcome within coherent sets. Distinguish visual matching, semantic identification and pairwise discrimination; do not require all of them in one pilot.

## Current progress (2026-09-29)

The [controlled recognition pilot](../../wiki/icon-recognition-pilot.md) now implements a 1.5-second 128-CSS-pixel target, then five candidates at assigned 6/8/10/12/14 sizes. Twenty targets × five sizes produce 100 randomized recorded trials, plus three practice. Keyboard/mouse input, confidence, recovery and exports are implemented and deployed. The previous runnable workflow is removed; old production pilots and results were deleted at the user’s request. Final stimulus consensus, calibration/familiarity decisions, approval/consent and analysis remain open. Production release `ec45d507` is verified; temporary synthetic records were removed.

## Acceptance criteria

- Approve an operational primary task: visual target matching or semantic naming as appropriate; keep their interpretations separate.
- Decide whether confidence is a final-study secondary measure; the usability prototype records it for selected-icon answers and omits it for unidentified responses.
- Decide whether a separate similarity/discrimination task is needed and feasible; the meeting did not finalize it.
- Add an optional short explanation prompt: which visual details influenced the answer?
- Specify participant instructions, trial order/randomization, stopping rules, and pilot size.
- Keep semantic interpretation as a human outcome, not as a computer-vision feature.
