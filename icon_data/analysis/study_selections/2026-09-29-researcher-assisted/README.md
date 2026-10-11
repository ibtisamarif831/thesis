# Algorithm-assisted stimulus nomination, 2026-09-29

The researcher requested selection and submission on their behalf without manually choosing icons. The September 17 session established the purpose: independent research-group nominations, comparison at the next meeting, then agreement on stimuli for a size-controlled pilot. The meeting did not finalize a sampling algorithm.

This nomination uses reviewer code `ibtisam`, renamed from `researcher-assisted` at the researcher's request. Its algorithm-assisted provenance remains recorded here and in the database rationale. It contains 20 icons from each of the five retained source sets, 100 total. Supervisor choices were not used to choose these icons. This is neither participant data nor an independent human rating, measurement validation, final consensus set, or authorization to run the pilot.

## Selection method

Each source is sampled independently from the authenticated production D1 catalog, matched against local canonical IDs, labels, normalized images, and features. Candidates with uncertain masks or non-finite representative features are excluded. Images must be 256×256, have at least eight pixels with some RGB channel below 245 after composition on white, and have unique RGBA pixel hashes within the source. This excludes three white AIGA assets invisible on white in addition to the existing 252 uncertain-mask exclusions.

The six scalar representatives use within-set midrank percentile differences; constant scalars are omitted. Reliable orientation uses axial angular difference divided by π/2. Orientation is omitted for a pair if either confidence is below the registry threshold (0.20). Distance is the RMS of available channels. Percentile scaling balances channel ranges but can emphasize tiny numeric differences, especially in visually uniform sets; pairwise omission of orientation compares different channel subsets. These exploratory distances are sampling aids, not a validated perception metric, and differ from the dashboard's standardized PCA projection.

For each set, select four disjoint pairs from the lowest quartile of distances, diversifying successive pairs across the feature space. Then select one remaining medoid and eleven greedy farthest-point coverage icons. Stable ascending icon IDs break ties. There is no AI embedding or semantic-category sampling. A contact-sheet rendering check was performed by the assistant; no independent human visual review was performed.

Eligible candidate counts after exclusions: AIGA 77, OCHA 207, Healthcare 45, ISO 7010 37, ISO 15223 28. All ISO 7010 orientations are confidence-undefined and contribute no orientation distances. Feature validation and consensus decisions remain pending.

## Files and reproduction

- `catalog.json`: production catalog snapshot with verified local paths and the seven feature IDs.
- `submission.json`: selected stable IDs and reviewer code in the dashboard's submission contract.
- `selection.csv`: ordered icons, reasons, close-pair partners/distances, raw measurements, and image hashes.
- `method.json`: source hashes, method, exclusions, ranges, coverage diagnostics, and limitations.
- `receipt.json`: production submission identity and verification status.
- `reproduce.py`: deterministic local selection; has no network writes.

From the repository root:

```sh
.venv/bin/python icon_data/analysis/study_selections/2026-09-29-researcher-assisted/reproduce.py
```

Submission used authenticated Wrangler administrative access to the existing production `glyph-study-selections` database. It inserted a fresh submission and its 100 selection rows, with an algorithm-assisted provenance note in the existing `rationale` field. It did not change the API, deploy assets, or replace any existing reviewer. The dashboard Results/CSV view exposes the reviewer code; its current result endpoint does not export the rationale. Compare against human nominations separately and label this method when reporting any overlap.
