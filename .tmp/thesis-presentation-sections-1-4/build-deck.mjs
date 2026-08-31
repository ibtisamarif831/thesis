import fs from "node:fs/promises";
import path from "node:path";
import { Presentation, PresentationFile } from "@oai/artifact-tool";

const ROOT = "/Users/macbook/thesis";
const TMP = path.join(ROOT, ".tmp/thesis-presentation-sections-1-4");
const OUT = path.join(ROOT, "presentations/perception-of-glyphs-progress-presentation.pptx");
const COVER_DIR = path.join(TMP, "paper-covers");
const RENDER_DIR = path.join(TMP, "rendered-full");
const DASHBOARD_DIR = path.join(ROOT, ".tmp/thesis-presentation-full/dashboard");

const C = {
  ink: "#111111",
  muted: "#5E6672",
  rule: "#B8BCC4",
  panel: "#F1F2F3",
  panelBlue: "#EAF5FB",
  accent: "#3D8DFF",
  accentLight: "#6DCBF4",
  white: "#FFFFFF",
};

const FONT = "Helvetica Neue";

function addText(slide, text, position, options = {}) {
  const box = slide.shapes.add({
    geometry: "textbox",
    position,
    fill: "none",
    line: { style: "solid", fill: "none", width: 0 },
  });
  box.text = text;
  box.text.style = {
    fontSize: options.fontSize ?? 22,
    typeface: FONT,
    color: options.color ?? C.ink,
    bold: options.bold ?? false,
    alignment: options.alignment ?? "left",
    verticalAlignment: options.verticalAlignment ?? "top",
  };
  return box;
}

function addRect(slide, position, fill, lineFill = "none", lineWidth = 0) {
  return slide.shapes.add({
    geometry: "rect",
    position,
    fill,
    line: { style: "solid", fill: lineFill, width: lineWidth },
  });
}

function addSlideChrome(slide, section, page) {
  addText(slide, section, { left: 42, top: 35, width: 330, height: 24 }, {
    fontSize: 15,
    bold: true,
    color: C.accent,
  });
  addText(slide, String(page).padStart(2, "0"), { left: 1180, top: 665, width: 58, height: 20 }, {
    fontSize: 13,
    alignment: "right",
    color: C.muted,
  });
}

function addTitle(slide, title, top = 78, height = 80, fontSize = 43) {
  return addText(slide, title, { left: 42, top, width: 1196, height }, {
    fontSize,
    bold: true,
  });
}

function setSources(slide, sources, presenterNotes = []) {
  const notes = [
    ...presenterNotes,
    "",
    "[Sources]",
    ...sources.map((source) => `- ${source}`),
  ].join("\n");
  slide.speakerNotes.textFrame.setText(notes);
  slide.speakerNotes.setVisible(true);
}

async function addImage(slide, imagePath, position, options = {}) {
  const bytes = await fs.readFile(imagePath);
  return slide.images.add({
    blob: new Uint8Array(bytes),
    contentType: "image/png",
    alt: options.alt ?? path.basename(imagePath),
    fit: options.fit ?? "contain",
    position,
    ...(options.crop ? { crop: options.crop } : {}),
  });
}

async function main() {
  await fs.mkdir(RENDER_DIR, { recursive: true });
  await fs.mkdir(path.dirname(OUT), { recursive: true });

  const presentation = Presentation.create({ slideSize: { width: 1280, height: 720 } });

  // 1. Title — Codex Grid slide-01 silhouette.
  {
    const slide = presentation.slides.add();
    slide.background.fill = C.white;
    addText(slide, "THESIS PROGRESS PRESENTATION", { left: 42, top: 42, width: 620, height: 30 }, {
      fontSize: 18,
      bold: true,
      color: C.accent,
    });
    addText(slide, "Perception of Glyphs", { left: 42, top: 205, width: 1080, height: 125 }, {
      fontSize: 72,
      bold: true,
      verticalAlignment: "bottom",
    });
    addRect(slide, { left: 42, top: 371, width: 188, height: 5 }, C.accentLight);
    addText(slide, "When do glyph sets stop being discernible as size is reduced?", { left: 42, top: 414, width: 1030, height: 65 }, {
      fontSize: 30,
    });
    addText(slide, "Name · Programme · Bauhaus-Universität Weimar · Supervisor · August 2026", { left: 42, top: 588, width: 1080, height: 28 }, {
      fontSize: 18,
      color: C.muted,
    });
    setSources(slide, ["Supervisor-provided thesis title and project description supplied by the user."], ["Replace only the name, programme, and supervisor fields."]);
  }

  // 2. Problem — Codex Grid slide-08 split silhouette.
  {
    const slide = presentation.slides.add();
    slide.background.fill = C.white;
    addSlideChrome(slide, "01 · THE PROBLEM", 2);
    addTitle(slide, "When do reduced glyphs stop being discernible?", 78, 84, 45);
    addText(slide,
      "As size decreases:\n\nFine detail disappears\nInternal gaps close\nThin strokes weaken\nShape differences collapse",
      { left: 42, top: 201, width: 510, height: 177 },
      { fontSize: 24 });
    addText(slide,
      "Target outcome\n\nSmallest discernible size\n+\nVisual predictors of confusion",
      { left: 42, top: 421, width: 510, height: 141 },
      { fontSize: 22, color: C.muted });
    addRect(slide, { left: 610, top: 176, width: 628, height: 452 }, C.panel, C.rule, 1);
    addText(slide, "GLYPH SET · DECREASING DISPLAY SIZE", { left: 641, top: 205, width: 566, height: 26 }, {
      fontSize: 16, bold: true, color: C.accent, alignment: "center",
    });
    await addImage(slide, path.join(ROOT, "presentations/assets/hamming-size-reduction.png"),
      { left: 745, top: 245, width: 360, height: 262 },
      { alt: "Five sharp glyph shapes progressively reduced until their differences become difficult to see" });
    addText(slide, "Legg et al., 2017 · Figure 1", { left: 780, top: 514, width: 290, height: 21 }, {
      fontSize: 12, color: C.muted, alignment: "center",
    });
    addText(slide, "At what point do set members become confused?", { left: 658, top: 548, width: 532, height: 35 }, {
      fontSize: 20, bold: true, alignment: "center",
    });
    setSources(slide, [
      "Supervisor-provided thesis title and project description supplied by the user.",
      "papers/Glyph_Visualization_A_Fail-Safe_Design_Scheme_Based_on_Quasi-Hamming_Distances.pdf, Figure 1, p. 32.",
    ]);
  }

  // 3. Research aim and questions — Codex Grid slide-09 / slide-17 sequence silhouette.
  {
    const slide = presentation.slides.add();
    slide.background.fill = C.white;
    addSlideChrome(slide, "02–03 · AIM AND RESEARCH DIRECTION", 3);
    addTitle(slide, "The research goal is explicitly size-dependent", 78, 84, 44);
    addText(slide,
      "Primary aim · Size-dependent discernibility\nCurrent focus · Computational basis for glyph selection",
      { left: 42, top: 171, width: 1138, height: 83 },
      { fontSize: 23, color: C.muted });

    const questions = [
      ["GOAL", "Discernibility thresholds across display sizes"],
      ["NOW", "Seven feature families · clustering · candidate selection"],
      ["LATER", "Research questions · protocol · measures"],
    ];
    questions.forEach(([label, body], index) => {
      const top = 295 + index * 107;
      addText(slide, label, { left: 42, top, width: 100, height: 42 }, {
        fontSize: 24,
        bold: true,
        color: C.accent,
      });
      addText(slide, body, { left: 168, top: top - 1, width: 1000, height: 58 }, {
        fontSize: 25,
      });
      if (index < 2) addRect(slide, { left: 42, top: top + 76, width: 1196, height: 1 }, C.rule);
    });
    setSources(slide, ["wiki/thesis-overview.md", "wiki/evaluation-and-human-study.md"]);
  }

  // 4. Literature argument: sources that shaped the implemented system.
  {
    const slide = presentation.slides.add();
    slide.background.fill = C.white;
    addSlideChrome(slide, "04 · LITERATURE REVIEW", 4);
    addTitle(slide, "Literature shaped the system and guides the next phase", 78, 62, 40);
    addText(slide,
      "Five implementation influences · one human-evaluation review",
      { left: 42, top: 158, width: 1160, height: 58 },
      { fontSize: 21, color: C.muted });

    const groups = [
      ["MEASURABLE STRUCTURE", "Forsythe et al. (2003) · Garcia et al. (1994) · Borgo et al. (2013)", "Evidence for measurable visual concepts"],
      ["SET-RELATIVE SEPARATION", "Legg et al. (2016) · Fuchs et al. (2014)", "Distance · clustering · contour-aware selection"],
      ["HUMAN EVALUATION", "Fuchs et al. (2017)", "Task- and condition-dependent performance"],
    ];
    groups.forEach(([label, names, body], index) => {
      const top = 250 + index * 105;
      addText(slide, label, { left: 42, top, width: 280, height: 25 }, {
        fontSize: 14,
        bold: true,
        color: C.accent,
      });
      addText(slide, names, { left: 350, top: top - 2, width: 470, height: 54 }, {
        fontSize: 19,
        bold: true,
      });
      addText(slide, body, { left: 880, top: top - 2, width: 325, height: 54 }, {
        fontSize: 18,
        color: C.muted,
      });
      if (index < groups.length - 1) addRect(slide, { left: 42, top: top + 74, width: 1196, height: 1 }, C.rule);
    });
    addRect(slide, { left: 96, top: 579, width: 1088, height: 70 }, C.panelBlue);
    addText(slide, "Research gap · No size-dependent thresholds for heterogeneous icon sets",
      { left: 122, top: 598, width: 1036, height: 38 }, { fontSize: 19, bold: true, alignment: "center" });
    setSources(slide, [
      "papers/Forsythe-Measuring_cion_complexity_automated.pdf, pp. 4–7",
      "papers/Garcia-Development_validation_icons_abstractness.pdf, pp. 3–4, 11, 20",
      "papers/Glyph-based_Visualization_Foundations_Design_Guidelines_Techniques_Applications.pdf, pp. 7–10, 12, 16",
      "papers/Glyph_Visualization_A_Fail-Safe_Design_Scheme_Based_on_Quasi-Hamming_Distances.pdf, pp. 4–6",
      "papers/The_Influence_of_Contour_on_Similarity_Perception_of_Star_Glyphs.pdf, pp. 2–3, 6–8",
      "papers/A_Systematic_Review_of_Experimental_Studies_on_Data_Glyphs.pdf, pp. 1–17",
    ], [
      "Five papers directly shaped the current measurements and glyph-selection workflow. The 2017 systematic review informs the later study-design phase.",
      "Maguire et al. (2012) was reviewed as design context but is omitted from the main narrative because it did not materially determine the current image-feature implementation.",
    ]);
  }

  // 5. Evidence-to-feature mapping.
  {
    const slide = presentation.slides.add();
    slide.background.fill = C.white;
    addSlideChrome(slide, "04 · LITERATURE REVIEW", 5);
    addTitle(slide, "Visual concepts became measurable features", 78, 62, 40);
    addText(slide,
      "One directly examined measure · six project-defined proxies",
      { left: 42, top: 156, width: 1160, height: 56 }, { fontSize: 20, color: C.muted });

    addText(slide, "FAMILY", { left: 42, top: 235, width: 180, height: 22 }, { fontSize: 14, bold: true, color: C.accent });
    addText(slide, "LITERATURE BASIS", { left: 250, top: 235, width: 300, height: 22 }, { fontSize: 14, bold: true, color: C.accent });
    addText(slide, "IMPLEMENTED REPRESENTATIVE", { left: 590, top: 235, width: 330, height: 22 }, { fontSize: 14, bold: true, color: C.accent });
    addText(slide, "RELATION TO LITERATURE", { left: 960, top: 235, width: 250, height: 22 }, { fontSize: 14, bold: true, color: C.accent });
    addRect(slide, { left: 42, top: 268, width: 1196, height: 2 }, C.ink);

    const rows = [
      ["Complexity", "Forsythe et al. (2003)", "Canny edge density", "Directly examined"],
      ["Shape · Density", "Garcia et al. (1994) · Fuchs et al. (2014)", "Enclosure · Solid fill", "Project-defined proxies"],
      ["Stroke · Texture", "Legg et al. (2016)", "Orientation · Local texture", "Project-defined proxies"],
      ["Balance · Colour", "Borgo et al. (2013)", "Symmetry · Saturation", "Project-defined proxies"],
    ];
    rows.forEach(([family, source, metric, status], index) => {
      const top = 292 + index * 69;
      addText(slide, family, { left: 42, top, width: 180, height: 48 }, { fontSize: 17, bold: true });
      addText(slide, source, { left: 250, top, width: 300, height: 48 }, { fontSize: 16, color: C.muted });
      addText(slide, metric, { left: 590, top, width: 330, height: 48 }, { fontSize: 17, bold: true });
      addText(slide, status, { left: 960, top, width: 250, height: 48 }, { fontSize: 16, color: index === 0 ? C.accent : C.muted, bold: index === 0 });
      if (index < rows.length - 1) addRect(slide, { left: 42, top: top + 51, width: 1196, height: 1 }, C.rule);
    });

    addText(slide, "Forsythe sample · 68 random icons from 239 McDougall symbols",
      { left: 42, top: 564, width: 1196, height: 28 }, { fontSize: 16, color: C.muted });
    addRect(slide, { left: 130, top: 606, width: 1020, height: 49 }, C.panelBlue);
    addText(slide, "Thesis contribution · Seven reproducible measurements across 28,749 icons",
      { left: 154, top: 619, width: 972, height: 27 }, { fontSize: 19, bold: true, alignment: "center" });
    setSources(slide, [
      "papers/Forsythe-Measuring_cion_complexity_automated.pdf, pp. 4–7",
      "papers/Garcia-Development_validation_icons_abstractness.pdf, pp. 3–4, 11, 20",
      "papers/The_Influence_of_Contour_on_Similarity_Perception_of_Star_Glyphs.pdf, pp. 2–3, 6–8",
      "papers/Glyph_Visualization_A_Fail-Safe_Design_Scheme_Based_on_Quasi-Hamming_Distances.pdf, pp. 4–6",
      "papers/Glyph-based_Visualization_Foundations_Design_Guidelines_Techniques_Applications.pdf, pp. 7–10, 12, 16",
      "wiki/literature-and-evidence.md",
      "wiki/feature-system.md",
    ], [
      "The literature names the visual concepts. Except for Canny edge density, the exact formulas are project-defined proxies and still require human validation.",
      "The 239-icon source-set count is verified from the local McDougall corpus manifest and dataset provenance.",
    ]);
  }

  // 6. Literature-to-selection strategy.
  {
    const slide = presentation.slides.add();
    slide.background.fill = C.white;
    addSlideChrome(slide, "04 · LITERATURE REVIEW", 6);
    addTitle(slide, "Literature guides glyph selection", 78, 62, 40);
    addText(slide,
      "Literature → candidate selection     Participants → perceptual evidence",
      { left: 42, top: 156, width: 1160, height: 50 }, { fontSize: 20, color: C.muted });

    addRect(slide, { left: 426, top: 238, width: 1, height: 310 }, C.rule);
    addRect(slide, { left: 852, top: 238, width: 1, height: 310 }, C.rule);
    const columns = [
      [42, "LEGG ET AL. · 2016", "Multiple visual channels", "Feature distance · clustering\nClose vs. distant candidates"],
      [468, "FUCHS ET AL. · 2014", "Contour and fill effects", "Enclosure · solid fill\nControlled contrasts"],
      [894, "FUCHS ET AL. · 2017", "Task-dependent performance", "Dashboard-selected stimuli\nParticipant validation"],
    ];
    columns.forEach(([x, citation, finding, effect]) => {
      addText(slide, citation, { left: x, top: 245, width: 342, height: 24 }, { fontSize: 15, bold: true, color: C.accent });
      addText(slide, finding, { left: x, top: 298, width: 342, height: 92 }, { fontSize: 23, bold: true });
      addText(slide, "EFFECT ON THIS WORK", { left: x, top: 430, width: 342, height: 22 }, { fontSize: 14, bold: true, color: C.accent });
      addText(slide, effect, { left: x, top: 467, width: 342, height: 76 }, { fontSize: 17, color: C.muted });
    });

    addRect(slide, { left: 76, top: 584, width: 1128, height: 70 }, C.panelBlue);
    addText(slide, "Thesis contribution · Confusion thresholds as display size decreases",
      { left: 100, top: 603, width: 1080, height: 38 }, { fontSize: 21, bold: true, alignment: "center" });
    setSources(slide, [
      "papers/Glyph_Visualization_A_Fail-Safe_Design_Scheme_Based_on_Quasi-Hamming_Distances.pdf, pp. 4–6",
      "papers/The_Influence_of_Contour_on_Similarity_Perception_of_Star_Glyphs.pdf, pp. 2–3, 6–8",
      "papers/A_Systematic_Review_of_Experimental_Studies_on_Data_Glyphs.pdf, pp. 1–17",
      "wiki/evaluation-and-human-study.md",
    ], [
      "The implemented distance and clustering are inspired by set-relative comparison; they are not a replication of quasi-Hamming distance.",
      "Fuchs et al. (2014) reports task-specific contour and fill effects, not a universal accuracy benefit.",
      "The 2017 review informs study-design options but does not define a finalized protocol for this thesis.",
    ]);
  }

  // 7. Journey — verified from Git milestones.
  {
    const slide = presentation.slides.add();
    slide.background.fill = C.white;
    addSlideChrome(slide, "05 · RESEARCH JOURNEY", 7);
    addTitle(slide, "Analysis prepared glyph selection", 78, 74, 44);
    addText(slide, "Corpus → reliable features → comparable exploration → interpretable clusters",
      { left: 42, top: 158, width: 1050, height: 36 }, { fontSize: 21, color: C.muted });
    addRect(slide, { left: 118, top: 351, width: 1034, height: 5 }, C.rule);
    const stages = [
      ["JUNE", "Corpus + first pipeline", "13 icon sets\nNormalized images\nFirst extraction + dashboard"],
      ["JULY", "Feature repair", "Corrected semantics\nSchema v2\nShared feature registry"],
      ["EARLY AUG", "Comparable exploration", "Balanced sampling\nSaved AI runs\nSide-by-side comparison"],
      ["10 AUG", "Interpretability", "Lasso selection\nCluster summaries\nPost-hoc feature profiles"],
    ];
    stages.forEach(([date, label, body], index) => {
      const x = 54 + index * 303;
      addRect(slide, { left: x + 61, top: 328, width: 48, height: 48 }, C.accent, C.white, 4);
      addText(slide, date, { left: x, top: 244, width: 170, height: 28 }, { fontSize: 15, bold: true, color: C.accent, alignment: "center" });
      addText(slide, label, { left: x, top: 278, width: 170, height: 47 }, { fontSize: 20, bold: true, alignment: "center" });
      addText(slide, body, { left: x, top: 405, width: 170, height: 137 }, { fontSize: 15, alignment: "center", color: C.muted });
    });
    addText(slide, "Result · Controlled glyph selection basis—not a discernibility threshold",
      { left: 178, top: 590, width: 924, height: 43 }, { fontSize: 20, bold: true, alignment: "center" });
    setSources(slide, [
      "Git history: 4e5d7d64a (2026-06-01), c9616aed2 (2026-07-21), 31e075b7b (2026-07-28), fce7512f1 (2026-08-10)",
      "wiki/README.md",
      "wiki/dashboard-implementation.md",
    ]);
  }

  // 8. Corpus inventory and pipeline.
  {
    const slide = presentation.slides.add();
    slide.background.fill = C.white;
    addSlideChrome(slide, "06 · IMPLEMENTATION", 8);
    addTitle(slide, "Thirteen source sets provide 28,749 study candidates", 76, 58, 40);
    addText(slide, "Canonical records · stable IDs · duplicates and alternate exports excluded",
      { left: 42, top: 143, width: 1120, height: 32 }, { fontSize: 18, color: C.muted });

    const sets = [
      ["ARASAAC pictograms", "13,798", "icon_data/normalized_256/07_arasaac_pictograms/34349__538f5c60c0e1.png"],
      ["Blissymbolics", "5,825", "icon_data/normalized_256/06_blissymbolics/glow_to_a71766efec32__bdd3d700a657.png"],
      ["OpenMoji", "4,495", "icon_data/normalized_256/10_openmoji/1f63d__2050cd8b138d.png"],
      ["Mulberry symbols", "3,436", "icon_data/normalized_256/05_mulberry_symbols/great__0a451f42764a.png"],
      ["OCHA humanitarian icons", "359", "icon_data/normalized_256/04_ocha_humanitarian_icons/location_lockdown__2016ac27259a.png"],
      ["McDougall symbols", "239", "icon_data/normalized_256/01_mcdougall_symbol_icon_set/mcdougall_120__5fd942c5ed8c.png"],
      ["Mapbox Maki", "215", "icon_data/normalized_256/03_mapbox_maki_icons/laundry__90f4992b19a3.png"],
      ["Healthcare webfont", "144", "icon_data/normalized_256/09_universal_symbols_healthcare_webfont/i_mental_health__d5402667624c.png"],
      ["USP medication pictograms", "83", "icon_data/normalized_256/13_usp_pictograms_manual/41__be5d68a9174d.png"],
      ["AIGA / DOT signs", "80", "icon_data/normalized_256/02_aiga_dot_symbol_signs/aiga_groundtransportation__9f76b8dc9f07.png"],
      ["ISO 7010 safety signs", "37", "icon_data/normalized_256/11_iso_7010_safety_signs/iso_7010_w019__3fc360c5c4e5.png"],
      ["ISO 15223 medical devices", "29", "icon_data/normalized_256/12_iso_15223_medical_device_symbols/liquid_filter_with_pore_size__34bbb8f93e68.png"],
      ["GHS hazard pictograms", "9", "icon_data/normalized_256/08_ghs_hazard_pictograms/flame__e6a519ba8dd8.png"],
    ];
    addText(slide, "SOURCE SET + EXAMPLE", { left: 42, top: 188, width: 340, height: 24 }, { fontSize: 14, bold: true, color: C.accent });
    addText(slide, "ICONS", { left: 526, top: 188, width: 90, height: 24 }, { fontSize: 14, bold: true, color: C.accent, alignment: "right" });
    addText(slide, "SOURCE SET + EXAMPLE", { left: 646, top: 188, width: 340, height: 24 }, { fontSize: 14, bold: true, color: C.accent });
    addText(slide, "ICONS", { left: 1130, top: 188, width: 90, height: 24 }, { fontSize: 14, bold: true, color: C.accent, alignment: "right" });
    for (let index = 0; index < sets.length; index += 1) {
      const [label, count, imagePath] = sets[index];
      const col = index < 7 ? 0 : 1;
      const row = col === 0 ? index : index - 7;
      const x = col === 0 ? 42 : 646;
      const top = 216 + row * 56;
      addRect(slide, { left: x, top, width: 44, height: 44 }, C.panel);
      await addImage(slide, path.join(ROOT, imagePath), { left: x + 4, top: top + 4, width: 36, height: 36 }, { alt: `${label} example`, fit: "contain" });
      addText(slide, label, { left: x + 58, top: top + 10, width: 400, height: 25 }, { fontSize: 16, bold: true });
      addText(slide, count, { left: x + 474, top: top + 10, width: 100, height: 25 }, { fontSize: 16, bold: true, alignment: "right" });
      addRect(slide, { left: x + 58, top: top + 47, width: 516, height: 1 }, C.rule);
    }
    addRect(slide, { left: 42, top: 622, width: 1196, height: 37 }, C.panelBlue);
    addText(slide, "Stable ID  →  256 × 256 normalized image  →  seven feature measurements  →  interactive review",
      { left: 64, top: 630, width: 1152, height: 22 }, { fontSize: 17, bold: true, alignment: "center" });
    setSources(slide, [
      "icon_data/analysis/dataset.csv (28,749 rows; counts verified 2026-08-16)",
      "wiki/datasets-and-provenance.md",
      "wiki/pipeline.md",
    ], [
      "A usable icon record is the pipeline's canonical row: one selected source icon after dataset-specific duplicate and alternate-export rules are applied.",
      "The displayed examples are representative normalized icons; they do not imply that every set uses the same visual style.",
    ]);
  }

  // 9. Feature families.
  {
    const slide = presentation.slides.add();
    slide.background.fill = C.white;
    addSlideChrome(slide, "06 · IMPLEMENTATION", 9);
    addTitle(slide, "Seven families describe what may survive at small sizes", 78, 74, 41);
    addText(slide, "Candidate predictors of persistence—or confusion—at reduced sizes",
      { left: 42, top: 158, width: 1140, height: 55 }, { fontSize: 20, color: C.muted });
    const families = [["COMPLEXITY", "Canny edge density"], ["SHAPE", "Enclosure score v2"], ["STROKE", "Principal-axis orientation v2"], ["DENSITY / FILL", "Solid fill ratio v2"], ["BALANCE", "Horizontal symmetry v2"], ["COLOR", "Mean saturation v2"], ["TEXTURE", "Local texture variation v2"]];
    families.forEach(([family, metric], index) => {
      const col = index < 4 ? 0 : 1;
      const row = col === 0 ? index : index - 4;
      const x = col === 0 ? 42 : 638;
      const top = 256 + row * 88;
      addText(slide, family, { left: x, top, width: 190, height: 24 }, { fontSize: 15, bold: true, color: C.accent });
      addText(slide, metric, { left: x + 210, top: top - 2, width: 350, height: 34 }, { fontSize: 21, bold: true });
      addRect(slide, { left: x, top: top + 48, width: 555, height: 1 }, C.rule);
    });
    addRect(slide, { left: 638, top: 510, width: 555, height: 112 }, C.panelBlue);
    addText(slide, "Important boundary", { left: 658, top: 527, width: 180, height: 24 }, { fontSize: 16, bold: true, color: C.accent });
    addText(slide, "Candidate predictors only\nDiscernibility requires participant evidence",
      { left: 658, top: 558, width: 505, height: 52 }, { fontSize: 17, bold: true });
    setSources(slide, ["code/thesis_pipeline/features/registry.py", "wiki/feature-system.md", "wiki/literature-and-evidence.md"]);
  }

  // 10. Dashboard as research instrument.
  {
    const slide = presentation.slides.add();
    slide.background.fill = C.white;
    addSlideChrome(slide, "07 · CURRENT SYSTEM", 10);
    addTitle(slide, "Demo 1: inspect the seven feature families", 78, 62, 40);
    addText(slide, "Seven measurements · value-stratified examples",
      { left: 42, top: 151, width: 1140, height: 38 }, { fontSize: 19, color: C.muted });
    addRect(slide, { left: 42, top: 207, width: 1196, height: 438 }, C.panel, C.rule, 1);
    await addImage(slide, path.join(DASHBOARD_DIR, "feature-groups-focus.png"),
      { left: 54, top: 219, width: 1172, height: 414 }, { alt: "Feature Groups table with seven representative measurements", fit: "contain" });
    setSources(slide, [
      "icon_data/analysis/analysis_dashboard/index.html (served and browser-verified 2026-08-13)",
      "code/build_analysis_dashboard.py",
      "wiki/dashboard-ui.md",
    ], [
      "Open one family detail during the live demo to show value-stratified examples and the selected representative.",
    ]);
  }

  // 11. Clustering demo.
  {
    const slide = presentation.slides.add();
    slide.background.fill = C.white;
    addSlideChrome(slide, "07 · CURRENT SYSTEM", 11);
    addTitle(slide, "Demo 2: inspect clustering", 78, 48, 40);
    addText(slide, "Lasso selection · cluster summaries · candidate contrasts",
      { left: 42, top: 151, width: 1140, height: 38 }, { fontSize: 19, color: C.muted });
    addRect(slide, { left: 42, top: 202, width: 1196, height: 456 }, C.panel, C.rule, 1);
    await addImage(slide, path.join(DASHBOARD_DIR, "clustering-focus.png"),
      { left: 54, top: 208, width: 1172, height: 444 }, { alt: "Clustering view with lasso controls and cluster summaries", fit: "contain" });
    setSources(slide, [
      "icon_data/analysis/analysis_dashboard/index.html (served and browser-verified 2026-08-13)",
      "code/build_analysis_dashboard.py",
      "wiki/dashboard-ui.md",
    ], [
      "During the live demo, use lasso selection, inspect one icon, and open one cluster summary.",
      "The dashboard supports candidate selection; it does not measure discernibility.",
    ]);
  }

  // 12. Representation comparison.
  {
    const slide = presentation.slides.add();
    slide.background.fill = C.white;
    addSlideChrome(slide, "07 · CURRENT SYSTEM", 12);
    addTitle(slide, "Demo 3: compare feature and AI groupings", 78, 62, 39);
    addText(slide, "Pairwise agreement · 0.783     Partition similarity—not accuracy",
      { left: 42, top: 151, width: 1140, height: 38 }, { fontSize: 19, color: C.muted });
    addRect(slide, { left: 63, top: 201, width: 1154, height: 456 }, C.panel, C.rule, 1);
    await addImage(slide, path.join(DASHBOARD_DIR, "feature-vs-ai-focus.png"),
      { left: 75, top: 213, width: 1130, height: 432 }, { alt: "Feature-based and AI embedding clustering comparison", fit: "contain" });
    setSources(slide, [
      "icon_data/analysis/analysis_dashboard/index.html (served and browser-verified 2026-08-13)",
      "code/thesis_pipeline/ai_clustering/metrics.py",
      "wiki/dashboard-ui.md",
      "wiki/similarity-and-clustering.md",
    ], [
      "Pairwise agreement compares every icon pair: whether both clusterings put the pair together or both put it apart.",
      "The AI image-embedding model receives normalized image pixels, not the seven thesis feature values.",
    ]);
  }

  // 13. Honest progress boundary.
  {
    const slide = presentation.slides.add();
    slide.background.fill = C.white;
    addSlideChrome(slide, "08 · CURRENT PROGRESS", 13);
    addTitle(slide, "The current system is ready for glyph selection", 88, 66, 39);
    addText(slide, "BUILT AND WORKING", { left: 42, top: 193, width: 450, height: 28 }, { fontSize: 16, bold: true, color: C.accent });
    addText(slide, "NEXT WORK", { left: 665, top: 193, width: 450, height: 28 }, { fontSize: 16, bold: true, color: C.accent });
    addRect(slide, { left: 626, top: 185, width: 2, height: 397 }, C.rule);
    const built = ["Icon corpus and normalization", "Seven feature families", "Interactive UI and lasso inspection", "Clustering and cluster summaries"];
    const pending = [
      ["01", "Select glyphs", "Feature values · clusters · summaries"],
      ["02", "Design the study", "Only after glyph selection"],
    ];
    built.forEach((item, index) => {
      const top = 251 + index * 79;
      addText(slide, "✓", { left: 42, top, width: 38, height: 30 }, { fontSize: 24, bold: true, color: C.accent });
      addText(slide, item, { left: 92, top: top + 1, width: 470, height: 36 }, { fontSize: 22, bold: true });
    });
    pending.forEach(([num, label, body], index) => {
      const top = 269 + index * 151;
      addText(slide, num, { left: 665, top, width: 46, height: 28 }, { fontSize: 16, bold: true, color: C.accent });
      addText(slide, label, { left: 729, top: top - 2, width: 460, height: 35 }, { fontSize: 24, bold: true });
      addText(slide, body, { left: 729, top: top + 41, width: 448, height: 67 }, { fontSize: 18, color: C.muted });
    });
    addText(slide, "Not yet defined · participant protocol · task · measurements",
      { left: 42, top: 611, width: 1196, height: 34 }, { fontSize: 23, bold: true, alignment: "center" });
    setSources(slide, ["wiki/README.md", "wiki/evaluation-and-human-study.md", "wiki/limitations-and-backlog.md"]);
  }

  // 14. Next phase.
  {
    const slide = presentation.slides.add();
    slide.background.fill = C.white;
    addSlideChrome(slide, "09 · NEXT PHASE", 14);
    addTitle(slide, "Next: select glyphs, then design the study", 78, 82, 42);
    addText(slide, "Immediate milestone · reviewed, defensible glyph selection",
      { left: 42, top: 164, width: 1150, height: 50 }, { fontSize: 21, color: C.muted });
    addRect(slide, { left: 42, top: 271, width: 535, height: 275 }, C.panel, C.rule, 1);
    addRect(slide, { left: 661, top: 271, width: 535, height: 275 }, C.panel, C.rule, 1);
    addText(slide, "01", { left: 76, top: 305, width: 56, height: 30 }, { fontSize: 18, bold: true, color: C.accent });
    addText(slide, "Select candidate glyphs", { left: 76, top: 353, width: 450, height: 42 }, { fontSize: 27, bold: true });
    addText(slide, "Dashboard review\nSeven feature values\nClustering + lasso\nCluster summaries",
      { left: 76, top: 417, width: 446, height: 91 }, { fontSize: 19, color: C.muted });
    addText(slide, "02", { left: 695, top: 305, width: 56, height: 30 }, { fontSize: 18, bold: true, color: C.accent });
    addText(slide, "Design the user study", { left: 695, top: 353, width: 450, height: 42 }, { fontSize: 27, bold: true });
    addText(slide, "Research questions\nTask + conditions\nParticipant plan\nMeasurements",
      { left: 695, top: 417, width: 446, height: 91 }, { fontSize: 19, color: C.muted });
    addText(slide, "→", { left: 589, top: 370, width: 60, height: 50 }, { fontSize: 36, bold: true, color: C.accent, alignment: "center" });
    addRect(slide, { left: 159, top: 592, width: 962, height: 55 }, C.panelBlue);
    addText(slide, "Current boundary · user-study design remains open",
      { left: 179, top: 608, width: 922, height: 27 }, { fontSize: 20, bold: true, alignment: "center" });
    setSources(slide, ["wiki/dashboard-ui.md", "wiki/dashboard-implementation.md", "wiki/evaluation-and-human-study.md"], ["The study-design details are intentionally left open at this stage."]);
  }

  // 15. Literature-grounded study-design options.
  {
    const slide = presentation.slides.add();
    slide.background.fill = C.white;
    addSlideChrome(slide, "09 · NEXT PHASE", 15);
    addTitle(slide, "How prior research evaluated glyphs", 78, 62, 40);
    addText(slide, "Two participant studies · one systematic review", { left: 42, top: 154, width: 1140, height: 34 }, { fontSize: 20, color: C.muted });

    addRect(slide, { left: 426, top: 221, width: 1, height: 343 }, C.rule);
    addRect(slide, { left: 852, top: 221, width: 1, height: 343 }, C.rule);
    const options = [
      [42, "FUCHS ET AL. · 2014", "CONTROLLED EXPERIMENTS", "Three experiments\nTarget + eight alternatives\nLab and online samples", "Measure · choice, accuracy, time\nFollow-up · questionnaire in Exp. 3"],
      [468, "LEGG ET AL. · 2016", "PARTICIPANT SURVEY", "20 recruited · 19 analysed\n104 randomized glyph pairs", "Measure · 0–10 differentiation rating\nContext · no task"],
      [894, "FUCHS ET AL. · 2017", "SYSTEMATIC REVIEW", "64 controlled-study papers\nQuantitative glyph tasks", "Output · task and measure taxonomy\nNo new participant experiment"],
    ];
    options.forEach(([x, citation, method, prior, adaptation]) => {
      addText(slide, citation, { left: x, top: 229, width: 342, height: 24 }, { fontSize: 15, bold: true, color: C.accent });
      addText(slide, method, { left: x, top: 276, width: 342, height: 34 }, { fontSize: 22, bold: true });
      addText(slide, "STUDY DESIGN", { left: x, top: 340, width: 342, height: 20 }, { fontSize: 13, bold: true, color: C.accent });
      addText(slide, prior, { left: x, top: 372, width: 342, height: 80 }, { fontSize: 17 });
      addText(slide, adaptation, { left: x, top: 482, width: 342, height: 70 }, { fontSize: 16, color: C.muted });
    });

    setSources(slide, [
      "papers/The_Influence_of_Contour_on_Similarity_Perception_of_Star_Glyphs.pdf, pp. 9–10",
      "papers/Glyph_Visualization_A_Fail-Safe_Design_Scheme_Based_on_Quasi-Hamming_Distances.pdf, pp. 4–5, 8",
      "papers/A_Systematic_Review_of_Experimental_Studies_on_Data_Glyphs.pdf, pp. 11–12",
      "wiki/literature-and-evidence.md",
      "wiki/evaluation-and-human-study.md",
    ], [
      "Fuchs et al. (2014) reported three controlled experiments. Experiment 1 used a target-plus-eight-alternatives similarity task with 12 novices and 12 experts; Experiment 2 was online; Experiment 3 collected accuracy, time, and a post-study questionnaire from 11 of 12 experts.",
      "Legg et al. recruited 20 Oxford students or employees; 19 responses were analysed. Participants rated 104 glyph pairs on an integer 0–10 differentiation scale, with the non-reference pairs randomized.",
      "Fuchs et al. (2017) is a systematic review, not a new participant experiment. It synthesized 64 papers with controlled quantitative glyph studies and categorized their tasks, measures, and outcomes.",
    ]);
  }

  // 16. Possible thesis study direction.
  {
    const slide = presentation.slides.add();
    slide.background.fill = C.white;
    addSlideChrome(slide, "09 · NEXT PHASE", 16);
    addTitle(slide, "Possible direction for the thesis study", 92, 86, 44);
    addRect(slide, { left: 42, top: 259, width: 188, height: 5 }, C.accentLight);
    const steps = [["01", "Control display size"], ["02", "Record accuracy and confusion"], ["03", "Ask which visual cues participants used"]];
    steps.forEach(([num, body], index) => {
      const top = 324 + index * 86;
      addText(slide, num, { left: 42, top, width: 68, height: 30 }, { fontSize: 18, bold: true, color: C.accent });
      addText(slide, body, { left: 128, top: top - 2, width: 1050, height: 47 }, { fontSize: 26, bold: true });
    });
    addText(slide, "Finalize after glyph selection + supervisor discussion", { left: 42, top: 620, width: 900, height: 29 }, { fontSize: 18, color: C.muted });
    setSources(slide, ["wiki/evaluation-and-human-study.md"], ["This is a discussion proposal only. The protocol, participant plan, sizes, stimuli, and measures are not finalized."]);
  }

  // 17. Conclusion.
  {
    const slide = presentation.slides.add();
    slide.background.fill = C.white;
    addSlideChrome(slide, "10 · CONCLUSION", 17);
    addTitle(slide, "A clear basis for the next research phase", 92, 86, 44);
    addRect(slide, { left: 42, top: 259, width: 188, height: 5 }, C.accentLight);
    const lines = [["01", "Icon corpus + seven feature families implemented"], ["02", "UI + clustering + summaries ready for glyph review"], ["03", "Next: glyph selection → user-study design"]];
    lines.forEach(([num, body], index) => {
      const top = 324 + index * 86;
      addText(slide, num, { left: 42, top, width: 68, height: 30 }, { fontSize: 18, bold: true, color: C.accent });
      addText(slide, body, { left: 128, top: top - 2, width: 1050, height: 47 }, { fontSize: 26, bold: true });
    });
    addText(slide, "Next milestone · a reviewed selection of candidate glyphs",
      { left: 42, top: 620, width: 760, height: 29 }, { fontSize: 18, color: C.muted });
    setSources(slide, ["wiki/thesis-overview.md", "wiki/evaluation-and-human-study.md", "wiki/limitations-and-backlog.md"]);
  }

  for (const [index, slide] of presentation.slides.items.entries()) {
    const stem = `slide-${String(index + 1).padStart(2, "0")}`;
    const png = await presentation.export({ slide, format: "png", scale: 1.5 });
    await fs.writeFile(path.join(RENDER_DIR, `${stem}.png`), new Uint8Array(await png.arrayBuffer()));
    const layout = await slide.export({ format: "layout" });
    await fs.writeFile(path.join(RENDER_DIR, `${stem}.layout.json`), await layout.text());
  }

  const montage = await presentation.export({ format: "webp", montage: true, scale: 1 });
  await fs.writeFile(path.join(TMP, "deck-montage-full.webp"), new Uint8Array(await montage.arrayBuffer()));

  const pptx = await PresentationFile.exportPptx(presentation);
  await pptx.save(OUT);
  console.log(OUT);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
