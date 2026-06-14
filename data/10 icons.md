# Thesis-Aligned Icon/Glyph Sets

Generated: 2026-06-09

This replaces the earlier mixed stimulus list. The older list contained useful cognitive-psychology picture sets, but food photos, affective photos, and 3D object models are weak matches for the thesis described in `agent.md`. For this thesis, the better target is icon/glyph material that is:

- symbol-like rather than photographic;
- available as SVG, font glyphs, or simple vector graphics;
- consistently drawn on a grid or within a style system;
- semantically labelled so icon meaning can be compared with visual form;
- suitable for computing visual complexity, abstractness, and pairwise distinguishability.

## Current Downloaded Sets

| # | Icon/glyph set | Domain | Scientific research use? | Why it fits or does not fit | Source / download |
|---:|---|---|---|---|---|
| 1 | McDougall Symbol/Icon Set | HCI / interface symbols | Yes | Best academic benchmark because it was explicitly normed for concreteness, complexity, meaningfulness, familiarity, and semantic distance. | Paper: https://link.springer.com/10.3758/BF03200730; open eprint: https://eprints.bournemouth.ac.uk/10165/ |
| 2 | AIGA / DOT Symbol Signs | Transportation / public wayfinding | Yes | Classic public pictograms developed through DOT/AIGA evaluation work and used in symbol-sign research. | Official AIGA page: https://www.aiga.org/resources/symbol-signs; Wikimedia category: https://commons.wikimedia.org/wiki/Category:AIGA_symbol_signs |
| 3 | Mapbox Maki Icons | Cartography / POI maps | Limited / not normed | Good cartographic glyph corpus, but not clearly a scientific stimulus set. | https://github.com/mapbox/maki |
| 4 | OCHA Humanitarian Icons | Humanitarian response / crisis maps | Limited / operational | Domain-specific and useful, but I found operational/public-communication evidence rather than controlled scientific norming. | https://un-ocha.github.io/humanitarian-icons/ and https://github.com/mapaction/ocha-humanitarian-icons-for-gis |
| 5 | OpenMoji | Emoji / pictographic communication | Indirect | Emoji are studied extensively, but I did not find strong evidence that OpenMoji itself is a normed scientific stimulus set. | https://openmoji.org/ and https://github.com/hfg-gmuend/openmoji |

## Better Scientific-Research Candidates From Different Domains

If the dataset must contain icon sets that were explicitly used, normed, or evaluated in scientific research, prioritize these:

| Candidate set | Domain | Why it belongs |
|---|---|---|
| ARASAAC pictograms | AAC / autism / communication accessibility | Normed and evaluated in studies of pictogram transparency, translucency, and AAC use. |
| ISO 7010 safety signs | Workplace safety / hazard prevention | Formal safety-sign standard; safety-sign comprehension is empirically studied. |
| GHS / OSHA hazard pictograms | Chemical hazards / lab safety | Used in hazard-communication comprehension studies; small, distinct domain set. |
| USP medication pictograms | Pharmacy / medication instructions | Evaluated in medication-use and health-literacy comprehension studies. |
| Universal Symbols for Healthcare / Hablamos Juntos | Healthcare wayfinding | Developed through a multi-year research and testing program; studied across cultures. |
| Blissymbolics | AAC / symbolic language | Long history in AAC learning, transparency, and symbolic-language research. |
| Mulberry Symbols | AAC / adult accessibility communication | Open SVG AAC set; recently studied for iconicity with other AAC symbol collections. |
| ISO 15223 medical-device symbols | Medical-device labeling | Standardized medical-label symbols tested for healthcare-provider comprehension. |

## How This Differs From The Previous List

The previous list mixed icons with standardized object/photo stimulus databases. For the thesis direction in `agent.md`, those should be treated as follows:

| Previous dataset | Keep for this thesis? | Reason |
|---|---|---|
| McDougall Symbol/Icon Set | Keep | Directly aligned with icon characteristics and norms. |
| Snodgrass & Vanderwart line drawings | Optional control set | Useful for visual complexity/naming literature, but object drawings are not interface glyphs. |
| BOSS photos | Drop from primary 10 | Photo objects are not glyphs/icons; useful only as a contrast set. |
| Moreno-Martinez & Montoro color photos | Drop from primary 10 | Object photos are not glyphs/icons. |
| Food-pics / Food Folio / CROCUFID | Drop | Food-photo stimuli are outside the glyph/icon thesis scope. |
| IAPS | Drop | Affective photos are outside the glyph/icon thesis scope and controlled access. |
| Peeters 3D objects / OpenVirtualObjects | Drop | Useful for VR object recognition, but not 2D glyph/icon design. |

## Best Next Dataset Plan

To make the dataset mostly scientific-research-used rather than mostly open/general-purpose, add ARASAAC, GHS/OSHA, USP medication pictograms, Universal Symbols for Healthcare, Blissymbolics, Mulberry, and ISO 15223/ISO 7010 sources where licensing allows.
