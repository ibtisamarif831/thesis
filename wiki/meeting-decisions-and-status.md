# Meeting decisions and verified current state

[Wiki home](README.md) · [Evaluation](evaluation-and-human-study.md) · [Current tasks](../tasks/current-thesis-next-steps.md)

Reviewed 2026-09-29 against the complete meeting transcript, current executable sources, generated artifacts, and authenticated production D1 reads. The source PDF was supplied in the September 17 session; its actual meeting date is not established by the transcript. Its mention of the next Tuesday at 11:00 is a historical appointment, not a current meeting schedule.

## Preserved meeting evidence

The full 39-page [original transcription PDF](../notes/meetings/standard-recording-2-transcription.pdf) and [page-marked text extraction](../notes/meetings/standard-recording-2-transcription.txt) are now retained in this repository. PDF SHA-256: `66ed48ab402e88f1001e5fe983820e1459ff41e15e97e73b5692474a64aadae6`. The transcription is imperfect and uses numbered speakers; do not infer speaker identities or treat uncertain terminology as a settled definition.

| Source location | Meeting direction | Status and interpretation |
|---|---|---|
| pp. 1–3, 00:31–05:50 | Define a clear research outcome and participant task. | Still requires a concise approved research question and operational task definition. |
| pp. 5–8, 09:10–14:52 | Computer-distance-based selection can bias a study; a global weighting may fail across styles. | Sampling and distance choices must be reported. Calibration is an empirical question, not an established result. |
| pp. 13–15, 26:04–29:53 | Narrow to small, coherent sets with a shared visual language. | Dashboard scope now contains five sources; comparisons should remain within a source. The full corpus is preserved. |
| pp. 17–19, 34:13–39:20 | Compare set-specific and pooled measures; focus first on scalability. | Possible analysis direction. Neither universal weights nor cross-set generalization has been demonstrated. |
| pp. 21–25, 42:41–48:40 | Showing a large icon first can prime recognition; identification differs from seeing that two icons differ; discuss matching against alternatives. | Final identification/discrimination/semantic task and exposure policy remain open. |
| pp. 27–31, 50:08–59:52 | Decide what the results mean; evidence-backed design guidance is a useful bounded outcome. | A predictive measure is an ambitious option, not a required guaranteed deliverable. Small or negative generalization results can still be informative. |
| pp. 32–35, 1:00:47–1:06:25 | Choose about 10–20 per set; start with identification; everyone nominates independently, then compare. Coverage versus close examples was debated. | No precise sampling algorithm was finalized. Five × 20 is a nomination target, not a fixed final-study trial count. |
| pp. 35–37, 1:05:52–1:08:11 | Provide separate per-set layouts/screenshots; agree final choices, then prepare scaling and a first pilot. | Implemented as Grid/Smart map with screenshots and stored nominations. Consensus stimuli remain pending. |
| pp. 37–38, 1:09:22–1:10:29 | Revisit what identification means: shape recognition versus semantics. | The usability prototype uses visual target matching; it does not settle the final thesis construct. |

## Current evidence, not meeting claims

Local CSV/JSON checks confirm 28,749 canonical rows across 13 sets, 28,749 feature rows with 133 columns, zero feature failures, seven configured representatives, 649 icons in the five-source dashboard, 397 quality-eligible Feature Groups rows and 252 uncertain-mask exclusions. Metadata/Combined contain 50 sampled rows. Similarity reports remain a historical 1,038-row run; their saved metadata, not today's preset, defines their measurements. The frozen benchmark has 450 rows and reports `blocked_pending_two_rater_benchmark` with `pilot_enabled: false`.

Production D1 nominations on 2026-09-29:

| Reviewer code | AIGA | OCHA | Healthcare | ISO 7010 | ISO 15223 | Total |
|---|---:|---:|---:|---:|---:|---:|
| `droa` | 20 | 20 | 20 | 20 | 20 | 100 |
| `pr77` | 20 | 20 | 20 | 10 | 10 | 80 |
| `ibtisam` | 20 | 20 | 20 | 20 | 20 | 100 |

The user identifies the first two as supervisor submissions. The database stores codes, not verified identities or review methods. `ibtisam` is the researcher-requested algorithm-assisted nomination, renamed from `researcher-assisted`; its [local audit](../icon_data/analysis/study_selections/2026-09-29-researcher-assisted/README.md) preserves the method. Compare it separately rather than counting it as a third independent human rating. Three additional codes beginning with `test` hold 17 rows in total; they remain untouched and require explicit classification before analysis. All six submissions together contain 297 nomination rows, including the smaller entries.

The separate [recognition usability pilot](icon-recognition-pilot.md) is implemented. Production contains two explicitly labeled, closed deployment-smoke-test pilots, one ended synthetic session, one answered practice attempt, and zero recorded attempts. These are engineering checks, not research participant data. This read-only audit created no pilots, sessions, submissions, or participant records.

The earlier deployed prototype showed a 128-CSS-pixel target for three seconds before a 20-icon candidate grid that the user can enlarge. It therefore includes exposure and memory effects discussed in the meeting. Its chosen size is a usability outcome, not an unprimed recognition threshold or a randomized assigned size condition. No final protocol approval is inferred from deployment.

The separate Overleaf checkout is clean at `e97751b` and matches its locally recorded `origin/main` (zero commits ahead/behind). Its Introduction draft is present; Related Work and remaining chapter placeholders still need writing. The existing 13-page PDF has a September 3 creation date, older than the September 18 source commit, so it is not verification of the latest source. No LaTeX sources were edited or rebuilt in this audit.

## Next work

1. Compare the two supervisor nominations and the computational nomination, classify the small test entries, and agree a final same-set stimulus list with reasons. Raw selections are not consensus.
2. Agree a primary task and useful result with the supervisors. Distinguish visual matching, semantic identification, pair discrimination, and qualitative explanation. Define how the exposure/memory issue will be controlled.
3. Complete the two-rater measurement benchmark before claiming validated features. Review the usability prototype's instructions, sizes, rendering, duration and logging; deployment itself does not satisfy this gate or institutional requirements.
4. Freeze study stimuli, computer-score exports, protocol, approvals/consent, exclusion rules and analysis. Collect human evidence only under that agreed design.
5. Analyze within-set size effects and human-computer agreement, and test generalization only where data and scope support it. Use the results for bounded design guidance.

## Documentation audit scope

The current status, checklist, task tickets, study plan, wiki, operational READMEs and thesis handoff were checked for contradictory current-state claims and local links. The audit updated 35 Markdown files (including this evidence page). It corrected obsolete checklist dates, candidate populations, benchmark/prototype distinctions, nomination progress, removed heatmap controls, unsafe default similarity/catalog-seed instructions, and the clean committed Overleaf source state. Dated literature notes and upstream dataset documentation remain historical evidence, not substitute status files. This audit verifies documentation against the inspected sources; it is not a new feature-validation study, complete statistical evaluation, browser regression run, or approval of the final research design.

Wiki pages updated in this audit: [dashboard-implementation.md](dashboard-implementation.md), [pipeline.md](pipeline.md), [similarity-and-clustering.md](similarity-and-clustering.md), [limitations-and-backlog.md](limitations-and-backlog.md), [README.md](README.md), [evaluation-and-human-study.md](evaluation-and-human-study.md), [icon-recognition-pilot.md](icon-recognition-pilot.md), [thesis-overview.md](thesis-overview.md), [artifacts-and-data-contracts.md](artifacts-and-data-contracts.md), [dashboard-ui.md](dashboard-ui.md), [repository-architecture.md](repository-architecture.md), [literature-and-evidence.md](literature-and-evidence.md), [commands-and-scripts.md](commands-and-scripts.md), and this meeting evidence page.

## New meeting: recording 4 (organized 2026-10-11)

The [organized summary and prioritized tasks](../notes/meetings/standard-recording-4-summary-and-tasks.md) preserve the [new transcript](../notes/meetings/standard-recording-4-transcription.pdf). The actual meeting date and speaker identities are not established. The revised pilot direction is five answer options (target, two computationally similar alternatives, two dissimilar), assigned sizes 6/8/10/12/14 CSS px, about 1.5 seconds exposure, 20 targets × five sizes = 100 randomized recorded trials per single-set pilot, and keys 1–5. Familiarity/preview policy, distance cutoffs, display calibration, and final-study burden remain open.

Implementation update on 2026-10-11: current local pilot sources implement the controlled version, with five candidates, 1.5-second exposure, three practice and 100 recorded fixed-size trials. The enlargement workflow is removed; old invitations return 410 while saved records remain exportable. This local change has not been deployed. See the [pilot contract](icon-recognition-pilot.md). The earlier verified production snapshot above has not been refreshed. The new notes do not establish participant results or supersede the feature-validation gate.
