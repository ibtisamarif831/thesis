# Evaluation Layer

This folder stores the thesis evaluation design and future evaluation scripts.

The feature extraction pipeline answers:

> What visual properties can the computer measure from each glyph/icon?

The evaluation layer answers:

> How do those computer-measured visual properties relate to human identification, similarity, confusability, and scale robustness?

The active visual feature families remain:

- Complexity
- Shape/silhouette
- Stroke/structure
- Density/fill
- Balance/layout
- Color/contrast
- Texture

Evaluation layers sit above those families. They are not new feature families.

Current specification:

- `evaluation_layers.md`

Future scripts should go here when implemented, for example:

- `select_stimuli.py`
- `export_family_scores.py`
- `build_pairwise_study_items.py`
- `join_human_responses.py`
- `analyze_human_computer_agreement.py`
- `analyze_scale_robustness.py`
