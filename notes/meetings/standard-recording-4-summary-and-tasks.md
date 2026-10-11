# Meeting 4: organized summary and action items

Organized on 2026-10-11. The meeting date is not established by the transcript. Source: [13-page transcription PDF](standard-recording-4-transcription.pdf), with [page-marked extracted text](standard-recording-4-transcription.txt). Speaker identities and mistranscribed names are not inferred. Timestamps below refer to the recording.

## Summary

The meeting reviewed the recognition pilot and proposed a faster, more controlled visual-matching task. Participants could recognize tiny icons from the arrangement of white space rather than detailed content. This is an observation from informal trials, not a validated result. The central question is what kind of distinguishability the study should measure within a coherent icon set.

The agreed direction to try is a five-option task with assigned sizes, replacing participant-controlled enlargement. Twenty targets at five sizes produce 100 recorded trials per single-set pilot. The thesis should aim for evidence-backed guidance about designing distinguishable icon sets, with the scope of recommendations constrained by the tested sets and conditions.

## Decisions and concrete directions to try

| Topic | Meeting direction | Recording |
|---|---|---|
| Answer display | One horizontal row of five icons instead of the existing 20-option grid. | 03:28–04:42; 08:28–08:55 |
| Sizes | Assign 6, 8, 10, 12 and 14 pixels; remove enlargement controls. | 07:10–07:21; 13:23; 14:43–15:12 |
| Exposure | Shorten the target exposure; 1.5–2 seconds discussed, with 1.5 seconds the stated working proposal. | 07:40–08:28 |
| Trial count | Each of 20 target icons appears once at each of five sizes: 100 recorded trials per set. Practice count was not settled. | 07:21; 14:43–15:12 |
| Alternatives | Target plus two alternatives with similar computed metrics and two with dissimilar metrics. Exact distance, scaling and cutoffs remain to be defined. | 04:01–04:19; 08:35–08:55 |
| Dataset scope | Keep each pilot within one icon dataset, using its 20-icon pool. | 13:48–14:10 |
| Ordering | Randomize the icon-size trials rather than running ascending size stages. | 15:25–15:30 |
| Input | Label options 1–5 and support corresponding number keys; retain clickable options. | 14:10–14:27; 17:48–17:57 |

These are meeting directions for a revised pilot, not implemented behavior or final-study approval. The exact layout of target presentation versus candidate presentation should be written explicitly before implementation; the discussion suggests keeping target-then-options but does not settle every display detail.

## Questions and exploratory hypotheses

- **Familiarity:** Should participants preview the full icon set first? Discuss with Patrick and the professor; preview versus no-preview conditions were suggested, not decided (16:05–17:25). Repeated targets will also create learning within a session.
- **Display calibration:** CSS pixels vary in physical/apparent size across displays. Credit-card calibration was discussed as cumbersome; no calibration solution was agreed (02:16–02:53). Fixed CSS sizes alone do not establish a universal physical-size threshold.
- **Task meaning:** Does matching white-space configuration count as the intended recognition? Define the outcome as visual matching unless a semantic task is explicitly chosen (00:00–00:50).
- **Complexity:** Icons with fewer components may be easier to distinguish (10:56–11:21).
- **Shape:** Elongated icons may be more confused with other elongated icons than with compact or round ones (11:21–12:34).
- **Background polarity:** Black versus white backgrounds may affect performance (12:43–12:57).
- **Meaningfulness:** Concrete/meaningful icons may differ from abstract ones (12:57–13:18). This requires independent metadata or human judgments; it is not an image-derived feature family.
- **Speed versus errors:** Keyboard input may reduce time but introduce accidental answers; check this in the pilot (18:01–18:11).

All these relationships remain hypotheses. Computed similarity is a selection rule, not evidence of human similarity.

## Prioritized task checklist

Owners below are suggested working assignments, not verified speaker identities.

### 1. Write the revised pilot specification — researcher, with supervisor review

- [ ] Specify the target-then-five-options sequence and settle 1.5 versus 2 seconds exposure.
- [ ] Specify five assigned sizes: 6, 8, 10, 12, 14 CSS px.
- [ ] Specify 20 targets × 5 sizes = 100 recorded trials per set; decide practice and breaks separately.
- [ ] Define similar/dissimilar alternative selection using a documented feature-distance rule, normalization and cutoffs; flag targets lacking suitable alternatives.
- [ ] Define trial randomization and candidate-position randomization. The latter is a recommended control; only trial-order randomization is explicit in the meeting.
- [ ] Resolve familiarity/preview policy with Patrick and the professor.
- [ ] Define the intended outcome and display/calibration scope.

### 2. Implement the revised pilot — researcher

- [ ] Add a versioned fixed-size protocol while retaining existing frozen pilot configurations and records.
- [ ] Generate 100 randomized recorded icon-size trials from one set.
- [ ] Show five candidates in one row, with the target present exactly once.
- [ ] Remove enlargement controls for this protocol.
- [ ] Add visible 1–5 labels, keyboard input and mouse selection; prevent repeated or premature key presses from answering subsequent trials.
- [ ] Update instructions, progress counts and completion summaries.

### 3. Make the responses analyzable — researcher

Recommended engineering fields, not a transcript-approved final schema:

- [ ] Log participant/session, trial ID, protocol version, dataset and target icon ID.
- [ ] Log assigned size, all five candidate IDs in displayed order, selected ID/position and correctness.
- [ ] Record exposure duration and response time with an explicit timing origin; retain display/viewport metadata and interruption events.
- [ ] Decide whether confidence remains on every trial; it was mentioned but not explicitly retained or removed in the revised design.
- [ ] Record familiarity/preview condition if used, and preserve stable joins to the seven representative features.

### 4. Test, share and review — researcher and research group

- [ ] Verify each target occurs once at every assigned size, trial ordering, correct-answer presence and input behavior.
- [ ] Run a small usability check: measure actual completion time, accidental responses, fatigue and whether 6–14 px spans useful performance levels.
- [ ] Share the revised pilot for comments before the next meeting.
- [ ] Confirm calendar dates: Thursday/Friday sharing and next Tuesday were mentioned (18:16–18:28), but no absolute dates are established.

### 5. Analyze pilot evidence before scaling up — researcher with supervisors

- [ ] Summarize accuracy by assigned size, target and set; inspect confusion choices and response times.
- [ ] Assess whether repeated observations support a defensible threshold estimate; define the accuracy criterion and uncertainty first. Five-choice chance accuracy is 20%.
- [ ] Explore associations with complexity, shape and background properties; separate exploratory findings from predeclared tests.
- [ ] Reassess the full-study burden. The meeting mentions 100 final icons, but does not approve a final trial design. Applying five sizes to all 100 would mean 500 recorded trials per participant.
- [ ] Translate supported results into bounded design guidance, rather than universal icon-design rules.

## Implementation at initial summary creation (before follow-up)

Checked on 2026-10-11 against `web/pilot/pilot.js` and `functions/lib/pilot.js`: the existing pilot still describes a three-second target, 20 candidates, three practice trials and 20 recorded trials, with participant-controlled enlargement. Its outcome remains size chosen before answering. The meeting's five-choice, assigned-size, 100-trial version is a backlog item, not completed work.

The existing two-rater feature-validation requirement remains separate. This meeting does not supply feature validation, research participant results or a completed human-computer comparison.

## Implementation follow-up — 2026-10-11

The controlled protocol is now implemented locally; see [current pilot contract](../../wiki/icon-recognition-pilot.md). The user requested removal of the old runnable workflow. Old invitations are retired, while historical records remain exportable. The implementation uses 1.5-second exposure, three practice trials at 14 px, confidence after selection and no full-set preview as explicit working choices. The historical checklist above records meeting-derived planning, not final-study approval. Hosted deployment, calibration/familiarity review and human usability evaluation remain separate.
