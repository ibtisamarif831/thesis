# Perception of Glyphs — Speaker Notes

Use this as a 12–15 minute script for the 17-slide **Progress Presentation**. Speak naturally rather than reading every word. The key boundary throughout is simple: the computer-side system is implemented; the human study and any claims about human discernibility remain future work.

## Slide 1 — Title

“Good [morning/afternoon]. My thesis is *Perception of Glyphs*. The central question is: when a set of glyphs is shown at progressively smaller sizes, when do its members stop being discernible from one another? Today I will show the computational basis I have built to prepare that study, and the evidence still needed from participants.”

Transition: “I will begin with why size reduction creates the problem.”

## Slide 2 — The problem

“A glyph can look clear at a large size but become difficult to distinguish when it is reduced. Fine detail can disappear, internal gaps can close, thin strokes can weaken, and different shapes can begin to look alike. The target outcome is therefore not only a smallest usable size, but also an explanation of which visual properties predict confusion within a glyph set.”

“The image on the right illustrates the idea of members of a set becoming harder to separate as their display size decreases.”

Transition: “That leads to the precise scope of the thesis.”

## Slide 3 — Aim and research direction

“The primary aim is size-dependent discernibility: estimating thresholds across display sizes. My current work does not yet measure those thresholds. It builds the computational basis for selecting glyphs and describing their visible properties consistently.”

“The current system gives me seven feature families, clustering, and candidate selection tools. The later phase will define the research questions, protocol, and participant measures.”

Transition: “The feature system did not start from arbitrary image metrics. It was shaped by the literature.”

## Slide 4 — Literature review: what informed the system

“The literature contributed in three different ways. First, work by Forsythe, Garcia, and Borgo supports the idea that some visual structure can be measured. Second, work by Legg and Fuchs informs set-relative separation, distance, clustering, and contour-aware candidate selection. Third, the Fuchs 2017 review shows that performance depends on the task and its conditions, which matters for the later participant study.”

“The gap I address is narrower: in the reviewed literature, I did not find size-dependent discernibility thresholds for heterogeneous icon sets.”

Transition: “I then translated these visual concepts into a small, traceable measurement system.”

## Slide 5 — Literature review: feature representatives

“This table makes an important distinction. The literature identifies the visual concepts, but it does not validate every formula used in this project. Canny edge density for complexity has direct measure-level precedent. The other six representatives are thesis-defined computational proxies.”

“For example, I use enclosure for shape, solid-fill ratio for density, orientation for stroke structure, horizontal symmetry for balance, mean saturation for color, and local texture variation for texture. They are useful candidate predictors, but they still require human validation.”

If asked why only seven: “The seven families give one interpretable representative per literature-informed visual concept. The broader raw feature export remains for traceability, not as an alternative thesis analysis.”

Transition: “The literature also shaped how I use these measurements.”

## Slide 6 — Literature review: from evidence to selection

“Legg’s work motivates considering multiple visual channels together. In this thesis, that informs feature distance, clustering, and the choice of close versus distant candidate glyphs. Fuchs 2014 shows that contour and fill effects can matter in particular tasks. That informs controlled contrasts using enclosure and solid fill.”

“The systematic review reminds us that task performance is condition-dependent. So the dashboard can help select stimuli, but only participants can provide perceptual evidence.”

“My intended contribution is to connect those controlled selections with confusion thresholds as display size decreases.”

Transition: “Next, I will briefly show the work completed so far.”

## Slide 7 — Research journey

“The work progressed in four stages. In June, I assembled the corpus and built an initial extraction and dashboard pipeline. In July, I repaired feature semantics and moved to the shared version-two registry. In early August, I made exploration more comparable through balanced sampling and saved side-by-side AI comparisons. By 10 August, I added lasso selection, cluster summaries, and post-hoc feature profiles.”

“The result is a defensible basis for controlled glyph selection. It is not yet a discernibility threshold.”

Transition: “Here is the scale of the implementation.”

## Slide 8 — Implementation: corpus and pipeline

“The corpus contains 13 icon sets and 28,749 canonical icon records. A canonical record means one selected source icon after each dataset’s duplicate and alternate-export rules have been applied. Each is normalized to a 256 by 256 image, assigned a stable identifier, measured with the seven representatives, and made available for interactive review.”

“The examples show the variety of source sets. They do not imply that all sources share the same visual style.”

Transition: “Those normalized images feed the seven interpretable families.”

## Slide 9 — Implementation: seven feature families

“These are the seven active families and their current representatives: complexity through Canny edge density; shape through enclosure; stroke through principal-axis orientation; density through solid fill ratio; balance through horizontal symmetry; color through mean saturation; and texture through local texture variation.”

“They describe visible image structure that may survive, or may collapse, at small sizes. They are candidate predictors only. The evidence for actual discernibility must come from participants.”

Transition: “I use the dashboard to inspect and select possible stimuli.”

## Slide 10 — Demo 1: feature families

“This view lets me inspect one representative measurement at a time. It shows examples sampled across the value range, so I can check whether a low, middle, or high value is visually plausible instead of trusting a number in isolation.”

“If I demonstrate it live, I will open one family detail and show the value-stratified examples. The purpose is quality review and candidate selection.”

Transition: “The next view adds relationships among icons.”

## Slide 11 — Demo 2: clustering

“This clustering view places icons according to the selected computer-side representation. I can lasso a group, inspect an individual icon, and open a cluster summary with the feature values. This helps identify candidate contrasts and potential confusions for later study design.”

“It is important not to overinterpret it: a cluster is a diagnostic grouping of computer-side data, not evidence that people will confuse those icons.”

Transition: “I also explored a comparison with image-embedding groupings.”

## Slide 12 — Demo 3: feature and AI groupings

“This saved example compares feature-based clustering with clustering based on AI image embeddings. The pairwise agreement is 0.783. That number means that, across all icon pairs, the two partitions often agree on whether a pair is together or apart.”

“It does not mean 78.3 percent accuracy, and it is not a human result. Most agreement can come from pairs that both methods keep apart. Also, the AI model receives normalized image pixels, not the seven thesis feature values.”

If asked about the low adjusted Rand score: “Adjusted Rand removes agreement expected from the partition structure; its lower value shows that the two grouping systems are not interchangeable.”

Transition: “So where does the project stand today?”

## Slide 13 — Current progress

“The computer-side foundation is built and working: the icon corpus and normalization, the seven feature families, the interactive dashboard and lasso inspection, and clustering with summaries.”

“The next work is deliberately separate. First I need a reviewed and defensible selection of glyphs. Only then can I finalize the participant protocol, task, and measurements.”

Transition: “This gives a clear next-phase sequence.”

## Slide 14 — Next phase

“The immediate milestone is to select candidate glyphs using the dashboard, the seven feature values, clustering, lasso inspection, and cluster summaries. Then I will design the user study around that controlled selection.”

“The protocol is intentionally still open. That is appropriate because the final stimuli, task conditions, participant plan, and measurements must be defined together and discussed with the supervisor.”

Transition: “Prior research gives useful options for that discussion.”

## Slide 15 — How prior research evaluated glyphs

“Fuchs 2014 used controlled experiments involving similarity choice, accuracy, time, and a follow-up questionnaire. Legg used a participant survey with 104 glyph pairs rated on a zero-to-ten differentiation scale. Fuchs 2017 is different: it is a systematic review of 64 quantitative glyph-study papers, rather than a new participant experiment.”

“Together, these show that similarity choice, differentiation ratings, accuracy, time, and qualitative feedback are all possible measures. They do not prescribe a final method for this thesis.”

If asked about Fuchs 2014 trial counts: “The paper has an internal inconsistency between a printed count and the implied experimental design, so I do not use an unqualified per-person trial count.”

Transition: “My current proposal combines the aspects most relevant to reduced-size discernibility.”

## Slide 16 — Possible thesis-study direction

“The proposal has three parts: control display size, record accuracy and confusion, and ask participants which visual cues they used. This would allow the final analysis to link observed confusion with both computer-side visual features and participant explanations.”

“But this is a discussion proposal, not a finalized protocol. The display sizes, stimuli, participant plan, and exact measures all require the next selection and supervisor discussion.”

Transition: “I will close with the current contribution and next milestone.”

## Slide 17 — Conclusion

“To conclude, I have implemented a large icon corpus and seven literature-informed feature families, together with an interface for reviewing candidates, clustering, and summaries. This creates a clear basis for the next research phase.”

“The next milestone is a reviewed selection of candidate glyphs. From there, I can design and pilot the size-controlled user study that will provide the human evidence required to answer the thesis question. Thank you. I welcome your questions and feedback on the study design and candidate-selection criteria.”

## Short answers for likely questions

### What is your thesis contribution at this stage?

“The contribution so far is a reproducible, literature-informed computational basis for selecting and describing glyph stimuli. The human-study contribution is the next phase.”

### Does clustering prove perceptual similarity?

“No. Clustering is a computer-side diagnostic tool. It helps form candidate groups and contrasts. Participant data is needed to test perceptual similarity or confusion.”

### Why are semantic meaning and familiarity excluded from the feature system?

“They matter to people, but they cannot be recovered reliably as visible pixel measurements. I treat them as possible metadata, controls, or participant outcomes rather than image-derived features.”

### What remains before data collection?

“A reviewed stimulus subset, a finalized task and size conditions, a response schema, supervisor approval, and a pilot. The measurement benchmark must also pass its two-rater release gate before those representatives are used in the pilot.”

### What does the AI comparison show?

“It compares two computer-side grouping approaches. It is useful for diagnosis, but it is neither human accuracy nor proof that an AI model understands the glyphs.”

## Delivery reminders

- Replace the title-slide placeholders for your name, programme, and supervisor if they are still visible.
- Keep the live demos brief. If the dashboard is not already running, present slides 10–12 as screenshots rather than debugging during the presentation.
- When discussing an unfinished item, say “planned”, “proposal”, or “next phase”; do not say “validated” or “proven”.
