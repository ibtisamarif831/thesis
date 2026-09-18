# Thesis document handoff

This file records the current state of the separate Overleaf/LaTeX thesis repository so another agent can continue the document work without confusing it with the main analysis repository.

## Important repository boundary

The thesis writing project is a separate Git repository at:

`/Users/macbook/thesis/6a8416f0e3507a1361793e2c`

Its remote is `origin/main`. Do not treat this directory as an ordinary folder of the analysis repository, and do not merge it into the outer repository. Push thesis-source changes from inside that directory only when explicitly requested.

## Current unpushed source changes

The nested repository is synchronized with `origin/main` at commit `89fd744` and currently has these uncommitted source changes:

- `main.tex` contains user metadata changes that predate the introduction draft; this task did not alter them.
- `text-source/introduction.tex` now contains a 1,496-word evidence-grounded first draft. It covers the motivation, literature-defined gap, aim and scope, computational foundation, planned comparison, contribution, and claim boundaries.
- `vr-thesis-template.bib` now contains verified entries for the six sources cited by the introduction. The `Kulik2011` sample entry is retained temporarily because the untouched Related Work placeholder still cites it.
- Final research questions and the thesis-structure roadmap remain source comments until the supervisor approves the meaning of discernibility, the participant task, and the later chapter structure.

The nested repository currently reports:

```text
 M main.tex
 M text-source/introduction.tex
 M vr-thesis-template.bib
?? .DS_Store
?? .gitignore
?? .vscode/
```

The untracked `.DS_Store`, `.gitignore`, and `.vscode/` entries also predate the introduction task and must be reviewed separately before any commit. Generated LaTeX files are kept under the ignored `build/` directory.

## Remaining metadata placeholder

The submission date in `main.tex` remains the template value `01st January 2000`. The other title-page fields currently contain non-template values from earlier user work. Do not infer a replacement submission date; change it only after the user confirms the correct value.

## Current chapter status

- `text-source/introduction.tex` — evidence-grounded first draft complete; rendered as five pages in the current template.
- `text-source/related-work.tex` — template placeholder with one sample citation.
- `text-source/abstract.tex`, `conclusion.tex`, and `appendix.tex` — template placeholders.
- `main.tex` — currently includes only Introduction, Related Work, Conclusion and Future Work, and Appendix as content chapters. Methodology, study, results, and discussion chapters have not yet been added or approved.

The current build command is `latexmk -pdf -interaction=nonstopmode -halt-on-error -outdir=build main.tex`. The verified build produced `build/main.pdf` with 13 pages and no unresolved citations or references. The template still emits pre-existing KOMA/`titlesec`, duplicate page-destination, declaration underfull-box, and long Conclusion heading warnings. Ordinary `\section` commands currently fail because of the template's KOMA/`titlesec` combination, so the introduction uses content-level KOMA `\minisec` headings without modifying the immutable template.

## What the thesis project contains

- `main.tex` — document entrypoint, title-page metadata, template structure, and chapter inputs.
- `text-source/abstract.tex` — abstract source.
- `text-source/introduction.tex` — introduction source.
- `text-source/related-work.tex` — related-work/literature source.
- `text-source/conclusion.tex` — conclusion source.
- `text-source/appendix.tex` — appendix source.
- `text-source/declaration-of-authorship.tex` — authorship declaration; preserve required wording.
- `images/` — thesis figures and image assets.
- `vr-thesis-template-preamble.tex` — university/template preamble; treat as immutable during ordinary writing.
- `vr-thesis-template.bib` — bibliography.

## Research direction to preserve

The thesis investigates when glyph sets remain discernible as display size is reduced. The primary experimental condition is decreasing pixel size. The computer-side pipeline supplies visible, pixel-derived feature-family measurements to help select and interpret glyphs; it does not directly measure human perception or semantic understanding.

The seven active visual families are complexity, shape/silhouette, stroke/structure, density/fill, balance/layout, color/contrast, and texture. Semantic meaning, familiarity, metaphor, culture, and learnability belong in metadata or human-study outcomes, not as image-derived feature families.

The human-study layer is still planned, not completed. Do not claim that participants, human ratings, significance tests, or human-computer agreement results already exist.

## Recommended continuation order

1. Inspect `main.tex` and all files under `text-source/` before editing.
2. Review the introduction with the supervisor and approve the meaning of discernibility and the primary participant task before adding final research questions or hypotheses.
3. Confirm the full chapter structure before adding the introduction roadmap or changing `main.tex`.
4. Replace the Related Work and remaining chapter placeholders while grounding literature claims in the local papers and verified bibliography.
5. Replace the submission-date placeholder only after the user confirms the factual value.
6. Compile from the nested repository with the verified `latexmk` command above and inspect the rendered PDF.
7. Run `git diff --check`, inspect the final diff, and commit only intentional source changes.
8. Push the nested repository to `origin/main` only after the user explicitly asks for that external update.

## Main analysis-repository references

For current evidence and project state, use:

- [Thesis status](THESIS_STATUS.md)
- [Thesis overview](wiki/thesis-overview.md)
- [Literature and evidence](wiki/literature-and-evidence.md)
- [Evaluation and human study](wiki/evaluation-and-human-study.md)
- [Thesis-writing guidance](https://github.com/ibtisamarif831/thesis/blob/master/agent.md)
