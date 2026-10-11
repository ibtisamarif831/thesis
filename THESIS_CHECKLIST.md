# Thesis completion checklist

Reviewed: 2026-09-29. Use [Thesis status](THESIS_STATUS.md), [current tasks](tasks/current-thesis-next-steps.md), and [meeting decisions and verified evidence](wiki/meeting-decisions-and-status.md) for current state. This replaces the obsolete June–July calendar; no new completion dates are inferred.

The thesis investigates size-dependent icon identification or discrimination within coherent source sets, using literature-informed computer measurements to support stimulus selection and later human-computer comparison. The final task definition and result remain subject to supervisor agreement.

## Computational foundation

- [x] Preserve the 13-source canonical corpus and provenance: 28,749 rows.
- [x] Normalize images and extract features for all canonical rows; verified feature failures are zero.
- [x] Organize seven literature-informed families and configure one representative per family.
- [x] Keep semantic meaning, familiarity and culture outside image-derived feature families.
- [x] Implement dashboard inspection and within-source Grid/Smart map nomination tools.
- [x] Implement feature-v2 benchmark tooling and mask overlays.
- [ ] Obtain two independent completed benchmark ratings and pass every feature release gate.
- [ ] Export final-study per-icon and pairwise scores with the chosen transformations and provenance. Existing 1,038-row similarity reports are historical, not this export.

## Nominations and consensus

- [x] Receive two supervisor-associated submissions: `droa` 100 icons and `pr77` 80.
- [x] Save `ibtisam`'s 100-icon algorithm-assisted nomination, with method and receipt.
- [ ] Compare supervisor selections and the computational nomination separately.
- [ ] Classify the smaller `test*` records before analysis; do not infer identity or delete them automatically.
- [ ] Agree and freeze a final same-set stimulus subset, recording stable IDs and reasons.
- [ ] Include suitable close and distant comparisons without claiming feature closeness proves human confusability.

## Research decisions and protocol

- [ ] Agree a concise research question and useful result, such as study-grounded design guidance.
- [ ] Define visual matching, semantic identification or pairwise discrimination as the primary task; keep their outcomes distinct.
- [ ] Define size conditions, exposure policy and controls for memory/large-image priming.
- [ ] Specify rendering, interpolation, background, CSS/physical-pixel interpretation and display requirements.
- [ ] Define sampling, trial order, repetitions, stopping rules, exclusions and missingness.
- [ ] Decide whether confidence, latency and retrospective qualitative explanations belong in the final study.
- [ ] Document the analysis and participant-count rationale after design agreement.
- [ ] Obtain required institutional approval and review consent/privacy materials before research recruitment.

## Usability prototype and human evidence

- [x] Implement anonymous matching sessions, progressive saves, interruption recovery, private summaries and exports.
- [x] Keep usability records separate from nominations and the two-rater measurement benchmark.
- [x] Verify engineering deployment using clearly labeled synthetic pilots.
- [ ] Review the existing prototype with supervisors: the controlled version shows a large target first, then five fixed-size candidates over 100 recorded trials. Its assigned CSS sizes do not by themselves establish a calibrated threshold.
- [ ] Run an approved human usability pilot and refine the protocol.
- [ ] Collect the research participant dataset. Current production checks contain only one synthetic answered practice trial and zero recorded attempts.
- [ ] Join exact stimulus IDs to computer measurements and analyze size effects, confusions, uncertainty and agreement/mismatch.
- [ ] Test set-specific versus pooled predictions only where the design supports it; do not guarantee global weights or causal feature attribution.

## Thesis writing

- [x] Preserve the Introduction first draft and bibliography in the separate Overleaf repository.
- [ ] Review the Introduction, final research questions and chapter structure with supervisors.
- [ ] Replace Related Work, Abstract, Conclusion and Appendix placeholders and add approved methodology/results/discussion chapters.
- [ ] Compile the latest thesis sources and check citations, references and layout. The existing 13-page PDF predates the latest source commit.
- [ ] Replace the template submission-date placeholder with a confirmed date.
- [ ] Complete final editing and supervisor review.

The two Git repositories remain separate. Commit or push only when explicitly authorized; this documentation audit does neither.
