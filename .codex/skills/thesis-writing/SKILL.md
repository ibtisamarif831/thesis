---
name: thesis-writing
description: Write or revise this thesis in Overleaf-compatible LaTeX using repository-grounded evidence, defensible citations, and verified claims.
---

# Thesis Writing

Use this skill when drafting, revising, structuring, or reviewing the user's thesis text in the local Overleaf project.

## Project locations

- Analysis and evidence repository: `/Users/macbook/thesis`
- Overleaf writing repository: `/Users/macbook/thesis/6a8416f0e3507a1361793e2c`
- Main LaTeX entrypoint: `/Users/macbook/thesis/6a8416f0e3507a1361793e2c/main.tex`
- Chapter sources: `/Users/macbook/thesis/6a8416f0e3507a1361793e2c/text-source/`
- Figures: `/Users/macbook/thesis/6a8416f0e3507a1361793e2c/images/`
- Bibliography: `/Users/macbook/thesis/6a8416f0e3507a1361793e2c/vr-thesis-template.bib`

The Overleaf folder is a separate Git repository. Do not merge it into the analysis repository or move files between them unless the user explicitly requests that integration.

## Required orientation

Before a substantive writing task, inspect the current files rather than relying on memory:

1. Read `/Users/macbook/thesis/AGENTS.md`, `agent.md`, and the relevant wiki page.
2. Read `/Users/macbook/thesis/THESIS_STATUS.md` and `wiki/thesis-overview.md` for research scope and status.
3. Read the relevant local evidence, normally `wiki/literature-and-evidence.md`, `wiki/evaluation-and-human-study.md`, `notes/paper_feature_review.md`, and extracted paper text.
4. Inspect the target `.tex` file and the current Overleaf repository status before editing.

For a short wording change, inspect the target text and the immediately relevant evidence; do not load the whole repository unnecessarily.

## Research and claim discipline

Classify each important sentence as literature evidence, project method, computed result, human-study result, interpretation, limitation, or future plan. Keep these categories visibly distinct.

- Never invent participants, human ratings, significance tests, validation results, or study outcomes.
- The human-study layer is not yet collected; write it as planned methodology or a gap, never as completed evidence.
- The seven dashboard representatives and 81 active features are computational measurements/proxies, not direct measurements of human perception.
- Semantic meaning, familiarity, metaphor, culture, and learnability are not image-derived feature families.
- Treat dashboard clustering and AI embedding results as diagnostic analyses, not proof of correctness or semantic understanding.
- Do not silently convert project-specific measurements into claims that a source paper validated the exact implementation.
- Preserve uncertainty, exclusions, sample definitions, and release-gate limitations when they affect the claim.

Use the local papers and bibliography first. Add a citation for non-trivial literature claims and keep citation keys consistent with the bibliography. If current external facts or a paper not present locally are required, browse authoritative sources and record the source before drafting.

## Writing behavior

- Match the user's requested tone and length; default to clear, direct academic prose rather than inflated language.
- Prefer one precise claim per sentence and define technical terms before using formulas.
- Keep the thesis narrative centered on reduced-size glyph discernibility, human identification/discrimination, and comparison with visible computer-measured feature families.
- Preserve the existing LaTeX structure unless restructuring is explicitly requested. Put chapter prose in `text-source/*.tex`; keep `main.tex` for document structure and metadata.
- The university template is immutable unless the user explicitly and separately authorizes a template change. Never alter `main.tex` structure, `vr-thesis-template-preamble.tex`, the document class, packages, fonts, page layout, title-page design, bibliography style, heading styles, or university formatting as part of ordinary thesis writing.
- Start writing by replacing placeholder prose in `text-source/introduction.tex`, then develop `text-source/related-work.tex`, `abstract.tex`, `conclusion.tex`, and `appendix.tex`. Keep the existing chapter structure. Add content with `\\section{...}` and `\\subsection{...}` inside the existing input files; do not add, remove, or reorder chapters in `main.tex` unless the user explicitly authorizes a content-structure change that is separate from template styling.
- Treat the example figure, sample hypothesis, placeholder title/author fields, and sample bibliography entry as template/example content, not thesis evidence. Replace example prose only in the appropriate content file. Do not modify the declaration of authorship casually; preserve its required wording and update only user-supplied factual fields when explicitly requested.
- If the user asks for an explanation only, answer in chat and make no file changes.

## Evidence-to-text workflow

For a new section, first identify its purpose, claims, evidence, and unresolved assumptions. Then draft the smallest section that satisfies that purpose. For results, link every number to a generated artifact or reproducible command. For methods, name the exact input, transformation, output, and limitation. For the human study, keep design targets separate from collected data.

When using dashboard evidence, check the current generator and generated metadata rather than copying stale prose. In particular, verify dataset counts, feature schema, representative features, sample definitions, uncertain-mask exclusions, cluster statistics, and AI-versus-manual metric meanings.

## Safe editing and verification

Before editing either repository, run `git status --short` and preserve unrelated user changes. Use `apply_patch` for local edits. Do not run `git reset`, discard files, or push to Overleaf unless explicitly requested.

After LaTeX edits:

1. Compile from the Overleaf repository with `latexmk -pdf main.tex`.
2. If compilation fails, inspect the first meaningful LaTeX error and fix only the scoped issue.
3. Check the generated PDF for page count, missing references, unresolved citations, overfull boxes, and obvious figure/layout problems. Use the PDF skill when visual PDF inspection is needed.
4. Run `git diff --check` and report the changed files, compilation result, and any remaining warnings.

For synchronization, pull before local work and push only after the user asks for the external update:

```bash
cd "/Users/macbook/thesis/6a8416f0e3507a1361793e2c"
git pull origin main
# edit and verify
git add <specific-files>
git commit -m "Describe the writing change"
git push origin main
```

Do not work simultaneously in the browser and local clone on the same lines; Overleaf Git integration is a single linear history.
