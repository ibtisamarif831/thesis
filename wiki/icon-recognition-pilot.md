# Controlled icon-recognition pilot

[Wiki home](README.md) · [Evaluation](evaluation-and-human-study.md) · [Meeting directions](../notes/meetings/standard-recording-4-summary-and-tasks.md)

## Current implementation — 2026-10-11

The only runnable protocol is `icon-recognition-controlled-v2`. The former self-selected-enlargement workflow has been removed. The user explicitly requested deletion of old results during release. Production v1 pilots, sessions and attempts were deleted after the record-preserving migration; their invitations now return 404. The protocol guard still returns 410 if a v1 snapshot exists in another environment. Reviewer nominations were preserved.

This is visual target matching from memory, not semantic naming, human feature validation or an automatically estimated recognition threshold. The feature-v2 two-rater gate remains separate. Synthetic checks do not establish research participant evidence. The controlled version is deployed as recorded below.

## Administration

Open **Pilot Studio** → **Submitted icon sets**, authenticate and refresh submissions. Each saved reviewer dataset with exactly 20 valid icons offers **Create pilot**. The dialog shows the icons, accepts a title and explains the fixed protocol; there is no size editor or legacy protocol selector. Creation freezes the submission/version, set, icon IDs, images, seven feature values, distance specification and candidate rankings. A concurrent nomination edit rejects creation. An unavailable or non-finite feature catalog blocks creation rather than selecting random alternatives.

Creating switches to **Pilot results**. Administrators can copy invitations, inspect configuration, view summaries, export CSV/full JSON, close pilots and delete closed pilots after confirmation. Production contains no old pilots or results. Close prevents new sessions while existing controlled sessions can finish. Deletion removes that pilot and its sessions/attempts atomically, including unfinished sessions, while retaining reviewer submissions. The key remains in memory only; participant invitations are random unlisted tokens.

## Participant protocol

Introduction → three practice trials → 100 randomized recorded trials → optional reflections → saved confirmation. All 20 images are decoded before starting. No full-set preview is shown. Practice targets are distinct, sampled from the same set, with candidates at 14 CSS px. Each recorded target appears exactly once at each of **6, 8, 10, 12 and 14 CSS px**. Thus there are 103 trials including practice, with indices 0–102.

Each trial begins with **Ready**, allowing rest between trials. The target appears alone at **128 CSS px for 1.5 seconds**, followed by one row of five options: target, two computationally nearest alternatives and two farthest alternatives. All five images use the assigned size, inside fixed 112 × 112-pixel buttons with 12-pixel gaps. Candidate positions are independently shuffled per trial; order of all 100 icon-size combinations is shuffled per session. Restarting an interrupted trial retains target, size and positions.

Options are labeled **1–5**. Participants click or press the corresponding number key. Selection locks the options and requests confidence 1–5, also using keys or mouse. Keyboard auto-repeat, held keys and a 150-ms confidence guard prevent one press from also rating confidence. **I cannot identify it** is a distinct answer with no confidence. Practice gives correctness feedback after save; recorded trials do not reveal correctness. There are no enlargement controls.

Every participant button displays a keycap badge. Enter on Windows/Linux or Return on Mac starts the session, starts a Ready trial, continues after practice, or retries a failed save. Keys 1–5 choose candidates and confidence; 0 records unidentified. Ctrl+Enter (Windows/Linux) or Command+Return (Mac) saves the final reflections, including while typing. Ctrl+Shift+X or Command+Shift+X ends the session, including while paused. Tab/Shift+Tab and native button activation remain supported; Enter activates the focused button before falling back to the current primary action. In reflection fields ordinary numbers and Enter remain text/newlines. Key repeats and held Enter cannot advance from session start into a trial or repeat a save. Badges are hidden from accessible names; `aria-keyshortcuts` and explicit confidence-button labels expose the controls to assistive technology.

The complete row and controls must fit without scrolling: minimum viewport 680 × 560 CSS px, plus measured container fit. Focus loss, hidden tabs, insufficient space and refresh interrupt unfinished attempts. The same trial restarts at Ready with a repeated-exposure flag. End session retains acknowledged answers. Reflections ask about task/pace, forgotten targets and helpful visual details, at most 1,000 characters each.

## Alternative selection

The published study catalog contains the seven representative measurements from the feature registry, not PCA coordinates as distance inputs. Scalar channels use population-standard-deviation normalization within the frozen 20-icon pool; constant scalars use scale 1. Principal-axis orientation uses the shortest modulo-180° angular difference divided by 90°. An equal-weight Euclidean combination ranks all 19 alternatives; stable icon ID breaks ties. The two nearest and two farthest are frozen for each target, with distances, scalar means/scales, feature IDs and selection rule saved for audit.

There is no absolute similarity cutoff. “Similar” and “dissimilar” mean relative computed ranks within this pool; they are not human similarity judgments. Feature validity, orientation confidence, candidate-pool selection bias and the suitability of this weighting still require review.

## Persistence and API contract

Sources: `functions/lib/pilot.js`, `functions/lib/controlled-pilot.js`, `functions/api/pilot*.js`, `web/pilot/`, and public bundle generator `code/build_public_dashboard.py`.

Migration `0002` creates pilot/session/attempt tables. **Migration `0003_controlled_pilot_trials.sql` is required**: it rebuilds only the attempt table with a 0–102 index bound, copies every existing row and recreates its uniqueness/index constraints. Parent pilots, sessions and reviewer nominations remain intact. Apply it before serving the new application; do not rerun the destructive catalog seed.

Pilot configuration and assigned session schedule are immutable JSON. The server validates assigned size, candidate membership, confidence, timing and input method, rejects enlargement, and computes correctness itself. Responses include target/candidate IDs, choice/position, assigned size, input method, confidence, duration and choice onset; response time is derived as duration minus choice onset. Duration and choice onset are client monotonic milliseconds from target exposure start; confidence entry is excluded. The choice onset captures the transition to the rendered candidate row rather than assuming the timer fired exactly at 1,500 ms. Browser rendering/timing is not laboratory precision.

All APIs use `no-store`; POSTs require same-origin JSON and bound request size. Session credentials are hashed server-side and retained only in tab sessionStorage. Participant configuration omits labels, features, alternative rankings and reviewer provenance. Recorded correctness is admin-only. Pending requests are persisted before sending; advance occurs only after acknowledgment. Identical retries are accepted; changed answers are rejected. Completion requires all **103** answers from the assigned schedule.

| Endpoint | Authorization and operations |
|---|---|
| `/api/pilots` | Admin: list/inspect/create/close/delete |
| `/api/pilot-sessions` | Invitation: info/create; own credential: resume; retired protocol returns 410 |
| `/api/pilot-trials` | Own credential: start/interrupt/answer |
| `/api/pilot-completion` | Own credential: complete all assigned trials or end early |
| `/api/pilot-results` | Admin: summary, `format=csv`, `format=full` |

## Results and interpretation

Summaries exclude practice and repeated-exposure recorded responses while retaining them in exports. Unidentified answers remain in the accuracy denominator. Results show assigned-size counts, per-size eligible N/correct/accuracy/unidentified and median response time, confidence, confusion choices and session status. Five-choice chance accuracy is 20%. Empty size conditions have null accuracy/latency, displayed as a dash. CSV additionally includes protocol/set, assigned size, candidate order, selected position, input method and timing; interrupted/unanswered trials obtain assigned size from the saved schedule. Full JSON includes frozen feature/selection metadata and schedules, omitting credential hashes. The exporter can read historical rows in isolated fixtures, but production historical results were deleted at the user’s request.

No physical calibration is applied. CSS sizes, viewing distance, target-first memory effects, repeated-target learning, practice familiarity and feature-based distractor selection limit interpretation. This implementation defaults to no full-set preview and retains confidence; these working choices still need supervisor review. A threshold criterion, uncertainty analysis, institutional protocol/consent and the final study size remain open.

## Verification and deployment

Build: `.venv/bin/python code/build_public_dashboard.py`.

```bash
node --test code/tests/pilot/validation.test.mjs
node code/tests/pilot/integration.mjs
```

The HTTP suite uses `wrangler.pilot-test.jsonc`, explicit local D1 binding and a fresh isolated `tmp/controlled-pilot-integration-d1-*` directory. It checks old-record retention through migration, 410 retirement, 103-trial completion, schedule uniqueness, fixed sizes, auth, idempotency, interruptions, early end, summaries/exports and nomination/deletion boundaries. Never execute this fixture seed against production.

Verified locally on **2026-10-11**: eight focused tests pass; the real-D1 HTTP suite completes all 103 trials and reconciles size summaries, retries, completion, retirement and old-record retention. The administrator browser creates the fixed protocol and renders empty size summaries correctly. `code/tests/pilot/controlled-browser.js` verifies the single five-option row, fixed 112-pixel hit cells, practice at 14 px, keyboard/repeat guards, mouse input, offline answer + refresh retry, stable interrupted assignments, recorded feedback suppression, unidentified and paused early exit. Its stored results reconcile to three practice answers, two recorded answers and one repeated-exposure exclusion. Network errors from deliberately aborted answer saves are expected in this recovery test.

For hosted release, preserve the existing production/preview binding isolation in `wrangler.jsonc`, apply migration 0003 with normal D1 migrations (after a backup), build, then deploy the public bundle and Functions together. Verify old-record counts before/after and new invitation flow. The controlled implementation is deployed as recorded below. Historical release IDs below refer to v1 only.

## Production release 2026-10-11

Deployed code commit `efd42f609` to Cloudflare Pages production (`master`), deployment [`ec45d507`](https://ec45d507.glyph-perception-dashboard.pages.dev). The [live Pilot Studio](https://glyph-perception-dashboard.pages.dev/pilot-studio.html) serves only the controlled experiment. Existing administrator secrets were preserved.

A private D1 backup and exact row snapshots were captured before schema changes. Migration 0003 first retained every row in all six application tables. Wrangler's migration-list wrapper returned API code 7403 while direct queries/export succeeded; the tested file was applied with `wrangler d1 execute glyph-study-selections --remote --file migrations/0003_controlled_pilot_trials.sql`, the 0–102 bound was verified, and `0003_controlled_pilot_trials.sql` was recorded in `d1_migrations` alongside 0001/0002.

At the user’s explicit request, both v1 pilots, their two sessions and three attempts were then deleted. Production smoke checks used a clearly marked temporary controlled pilot provisioned with an atomic nomination-snapshot guard. Live API checks verified the published catalog/manifest, 103-trial schedule, fixed-size save/retry, early end, missing old invitations and result authorization. The live browser verified five options, no enlargement, keyboard choice/confidence and saved early exit. Two synthetic practice answers were verified in D1; the temporary pilot and all its sessions/attempts were then removed.

Final remote verification: **649 catalog icons, three reviewer submissions, 280 nominations; zero pilots, zero participant sessions and zero attempts**. Every catalog/submission/nomination row matched the pre-release snapshot exactly. The destructive catalog seed was not run. Create a fresh controlled pilot from a saved 20-icon reviewer set; no synthetic invitations remain live. The final research-design and two-rater validation gates remain open.

## Historical implementation and release evidence (v1)

On 2026-10-06, the pilot-delete control was tested in isolated local D1 with administrator and origin checks, open-pilot rejection, closed-pilot deletion of sessions and attempts including an active session, 404 after deletion, and preservation of a separate pilot and reviewer submission. Browser checks verified cancellation and confirmed deletion of a synthetic local pilot. Production deployment `0ddb9631` serves the control and active-session warning; the delete endpoint rejected an unauthenticated request with 401. No production pilot was deleted during testing.

The smaller-size update defaults to 31 levels from 4 to 64 CSS pixels in steps of 2. Validation tests cover the 4-pixel minimum and 47-level limit; the isolated D1 suite verifies creation and persistence of the full 31-level enlargement sequence while retaining legacy configuration compatibility. A browser check rendered all 20 candidate images at every 2-pixel step, confirmed the fixed grid dimensions and disabled enlargement at 64 pixels, and saved the practice response. Production deployment `435b5065` serves the updated default size sequence. No migration or modification of existing pilot configurations is required.

The submission deletion and separate Pilot results tab were verified on 2026-09-29 against isolated local D1: admin/submit-key boundaries, same-origin enforcement, stale-delete rejection, cascade deletion and preserved frozen pilots/session summaries. Browser checks exercised creation switching tabs, deletion cancellation/confirmation, independent tab visibility, retained summaries and CSV/JSON downloads. Production deployment `4f64cad9` was verified through the live studio → Pilot results navigation and an unauthenticated deletion rejection (401). No production submissions were deleted during verification.

The Pilot Studio navigation addition was verified locally and in the production browser on 2026-09-29: dashboard link → studio landing page → administrator tab with the key field focused (initially Results; now Pilot results). Deployment `849b8ec5` publishes the 668-file bundle (including `_headers`); this navigation change requires no database migration.


## Release verification — 2026-09-29

Production deployment `9e5598a3-65c8-406a-ad3f-46396c56a67e` serves the rebuilt 667-file bundle, including 649 images. The additive production migration preserved every original record: five reviewer submissions and 197 ordered nominations. A concurrent new 100-icon submission was retained, bringing the verified production snapshot to six reviewers and 297 nominations; the catalog stayed at 649 icons. The destructive seed was not executed. Clearly named, closed deployment-smoke pilots retain one synthetic accepted practice response, separate from research data.

Verification passed the five focused validation tests, the real local-D1 HTTP suite (including nomination submission/replacement), isolated hosted preview smoke tests, private administrator UI creation/inspection/summary/download/closure, full 23-trial Chrome and WebKit runs, offline trial/final-save retry after refresh, image-preload failure and small-window early exit. Native Safari verified image readiness, target/grid display, enlargement, answer locking/confidence, saved practice feedback/early exit, hidden-tab interruption with Ready restart, and pause after minimizing the window. Headless tabs do not reliably reproduce OS focus/visibility changes; test those in a native desktop browser.

The existing production administrator secret was preserved rather than rotated. Authenticated administration was exercised in the isolated preview with test secrets. The production smoke pilot was provisioned directly in D1 with an atomic reviewer-snapshot guard because the encrypted production secret cannot be retrieved; participant APIs, stored records, unauthorized result access and the existing page/image routes were verified on production. No Git commit or push was made. The feature-v2 gate still reports `blocked_pending_two_rater_benchmark` and `pilot_enabled: false`.

## Full keyboard interaction update — 2026-10-11

`code/tests/pilot/keyboard-study-browser.js` exercises a complete shortened mock schedule entirely through keys, for Windows and Mac platform detection: begin, held-Enter guard, Ready, candidate/confidence, unidentified, failed-save retry, practice continue, reflection typing, final save and early end. It creates no participant records. The actual server protocol remains 103 trials. This UI update requires no database migration.

Published as production deployment [`b46388a7`](https://b46388a7.glyph-perception-dashboard.pages.dev), code commit `19b0c191e`. Live `pilot.js`/`pilot.css` exactly matched the tested build. The Windows/Mac keyboard browser flow also passed against hosted assets with participant APIs mocked, so no production sessions/results were created or changed.
