# Thesis document handoff

This file records the current state of the separate Overleaf/LaTeX thesis repository so another agent can continue the document work without confusing it with the main analysis repository.

## Important repository boundary

The thesis writing project is a separate Git repository at:

`/Users/macbook/thesis/6a8416f0e3507a1361793e2c`

Its remote is `origin/main`. Do not treat this directory as an ordinary folder of the analysis repository, and do not merge it into the outer repository. Push thesis-source changes from inside that directory only when explicitly requested.

## Current unpushed source change

The nested repository is synchronized with its remote at its last commit and has this uncommitted source change in `main.tex`:

- Title changed from `Title of the Thesis` to `Perception of Glyphs`.
- Subtitle changed from `Optional Subtitle of the Thesis` to `When do glyph sets stop being discernible as size is reduced?`.
- A final newline was added at the end of the file.

The nested repository currently reports:

```text
 M main.tex
?? main.aux
?? main.fdb_latexmk
?? main.fls
?? main.log
```

The `.aux`, `.fdb_latexmk`, `.fls`, and `.log` files are local LaTeX build outputs, not thesis source. Review them for diagnostics, but do not commit them unless the project’s repository policy explicitly changes.

## Template placeholders still present

The title page still contains template/example values that must be replaced with user-confirmed facts before submission:

- Author: `John Doe`
- Matriculation number: `123456`
- Birth date: `01st January 1900`
- Birthplace: `Atlantis`
- First referee: `Prof. Dr. Bernd Fröhlich`
- Second referee: `Prof. Dr. Elvin Gadd`
- Submission date: `01st January 2000`

Do not invent or infer these values. Ask the user and change only the fields they confirm.

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
2. Replace placeholder prose in the chapter source files, beginning with the introduction, while preserving the existing chapter structure.
3. Ground literature claims in the local papers, extracted text, and bibliography; distinguish literature evidence from project methods, computed results, interpretations, limitations, and future plans.
4. Replace title-page personal metadata only from user-confirmed facts.
5. Compile from the nested repository with `latexmk -pdf main.tex`.
6. Review the generated PDF for missing references, unresolved citations, overfull boxes, and obvious layout problems.
7. Run `git diff --check`, inspect the final diff, and commit only intentional source/artifact changes.
8. Push the nested repository to `origin/main` only after the user explicitly asks for that external update.

## Main analysis-repository references

For current evidence and project state, use:

- [Thesis status](THESIS_STATUS.md)
- [Thesis overview](wiki/thesis-overview.md)
- [Literature and evidence](wiki/literature-and-evidence.md)
- [Evaluation and human study](wiki/evaluation-and-human-study.md)
- [Thesis-writing guidance](https://github.com/ibtisamarif831/thesis/blob/master/agent.md)
