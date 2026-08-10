import fs from "node:fs/promises";
import path from "node:path";
import { Presentation, PresentationFile } from "@oai/artifact-tool";

const ROOT = "/Users/macbook/thesis";
const TMP = path.join(ROOT, ".tmp/thesis-presentation-sections-1-4");
const OUT = path.join(ROOT, "presentations/thesis-presentation-sections-1-4.pptx");
const COVER_DIR = path.join(TMP, "paper-covers");
const RENDER_DIR = path.join(TMP, "rendered");

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

function addSummaryBlock(slide, label, body, top, x = 42, width = 700) {
  addText(slide, label.toUpperCase(), { left: x, top, width, height: 24 }, {
    fontSize: 16,
    bold: true,
    color: C.accent,
  });
  addText(slide, body, { left: x, top: top + 29, width, height: 72 }, {
    fontSize: 19,
    color: C.ink,
  });
}

async function addPaperSlide(presentation, paper, page, imageRight = true) {
  const slide = presentation.slides.add();
  slide.background.fill = C.white;
  addSlideChrome(slide, "04 · LITERATURE REVIEW", page);
  addTitle(slide, paper.shortTitle, 70, 74, 40);
  addText(slide, paper.citation, { left: 42, top: 143, width: 1180, height: 30 }, {
    fontSize: 16,
    color: C.muted,
  });

  const textX = imageRight ? 42 : 478;
  const textWidth = 718;
  const imageX = imageRight ? 820 : 42;

  addRect(slide, { left: imageX, top: 188, width: 418, height: 438 }, C.panel, C.rule, 1);
  await addImage(slide, path.join(COVER_DIR, paper.cover), {
    left: imageX + 18,
    top: 202,
    width: 382,
    height: 410,
  }, { alt: `First page of ${paper.shortTitle}` });

  addSummaryBlock(slide, "Purpose", paper.purpose, 190, textX, textWidth);
  addSummaryBlock(slide, "Method", paper.method, 298, textX, textWidth);
  addSummaryBlock(slide, "Main finding", paper.finding, 406, textX, textWidth);

  addRect(slide, { left: textX, top: 529, width: textWidth, height: 97 }, C.panelBlue);
  addText(slide, "WHY IT MATTERS HERE", { left: textX + 20, top: 546, width: textWidth - 40, height: 20 }, {
    fontSize: 15,
    bold: true,
    color: C.accent,
  });
  addText(slide, paper.relevance, { left: textX + 20, top: 573, width: textWidth - 40, height: 42 }, {
    fontSize: 18,
  });

  setSources(slide, [paper.source], [paper.note]);
  return slide;
}

const papers = [
  {
    shortTitle: "Measuring icon complexity automatically",
    citation: "Forsythe, Sheehy & Sawey · 2003",
    cover: "Forsythe-Measuring_cion_complexity_automated.png",
    purpose: "Test whether image-processing measurements can estimate human judgments of icon complexity.",
    method: "Six pixel-derived properties were correlated with established human complexity ratings for a random sample of 68 icons.",
    finding: "Structural variability and edge information showed the strongest relationships with perceived complexity (ρ = .65 and .64).",
    relevance: "Provides the strongest direct basis for edge density and structural variability as computational complexity proxies.",
    note: "Keep the claim narrow: the paper supports complexity estimation, not semantic understanding.",
    source: "papers/Forsythe-Measuring_cion_complexity_automated.pdf, pp. 1–9",
  },
  {
    shortTitle: "Abstractness affects identification",
    citation: "Garcia, Badre & Stasko · 1994",
    cover: "Garcia-Development_validation_icons_abstractness.png",
    purpose: "Develop a quantitative abstractness–concreteness metric and test whether it matches users’ judgments and task performance.",
    method: "Different participant groups ranked abstract and concrete icon sets, matched icons to Pascal constructs, and completed context conditions.",
    finding: "The metric aligned with subjective judgments; concrete icons were identified better, and context changed identification performance.",
    relevance: "Shows that measurable structure matters, but meaning and context cannot be inferred reliably from pixels alone.",
    note: "This paper combines a structural metric with subjective ranking and identification tasks.",
    source: "papers/Garcia-Development_validation_icons_abstractness.pdf, pp. 1–21",
  },
  {
    shortTitle: "Glyph design needs perceptual foundations",
    citation: "Borgo et al. · 2013",
    cover: "Glyph-based_Visualization_Foundations_Design_Guidelines_Techniques_Applications.png",
    purpose: "Connect glyph visualization to semiotics, perception, design guidelines, implementation techniques, and application practice.",
    method: "A state-of-the-art review synthesizing foundations and design knowledge across glyph-based visualization research.",
    finding: "Shape, colour, texture, size, orientation, curvature, and grouping act as visual channels whose effectiveness depends on task and context.",
    relevance: "Provides the conceptual map for the thesis’s visual families while warning against treating feature distance as a complete perceptual model.",
    note: "This is a review and design synthesis, not a single controlled participant experiment.",
    source: "papers/Glyph-based_Visualization_Foundations_Design_Guidelines_Techniques_Applications.pdf, pp. 1–26",
  },
  {
    shortTitle: "Channel distance can reduce glyph confusion",
    citation: "Legg, Maguire, Walton & Chen · 2016",
    cover: "Glyph_Visualization_A_Fail-Safe_Design_Scheme_Based_on_Quasi-Hamming_Distances.png",
    purpose: "Adapt Hamming distance to glyph design so visually separable glyph sets can be designed more systematically.",
    method: "The authors define quasi-Hamming distance, estimate channel separability with a 20-participant survey, and demonstrate it in a file-event glyph system.",
    finding: "Increasing differences across visual channels can reduce vulnerability to perceptual errors, although separability varies by channel.",
    relevance: "Motivates pairwise distinguishability and family-wise distance, but does not validate the thesis’s exact continuous feature formulas.",
    note: "Present quasi-Hamming distance as an inspiration for set-relative distinguishability, not as the implemented metric itself.",
    source: "papers/Glyph_Visualization_A_Fail-Safe_Design_Scheme_Based_on_Quasi-Hamming_Distances.pdf, pp. 1–11",
  },
  {
    shortTitle: "A taxonomy can guide scalable glyph design",
    citation: "Maguire et al. · 2012",
    cover: "Taxonomy-Based_Glyph_Designwith_a_Case_Study_on_Visualizing_Workflows_of_Biological_Experiments.png",
    purpose: "Replace ad-hoc glyph creation with a systematic process that scales to many domain concepts.",
    method: "A design methodology combines a concept taxonomy, a hierarchy of visual channels, and a biological-workflow case study.",
    finding: "Structured categorization and deliberate visual-channel assignment can produce a more scalable, application-specific glyph language.",
    relevance: "Supports organizing semantic categories as metadata and design context—not claiming that low-level image features recover meaning.",
    note: "Keep taxonomy and semantic mapping outside the computer-vision feature families.",
    source: "papers/Taxonomy-Based_Glyph_Designwith_a_Case_Study_on_Visualizing_Workflows_of_Biological_Experiments.pdf, pp. 1–10",
  },
  {
    shortTitle: "Contours shift perceived similarity",
    citation: "Fuchs et al. · 2014",
    cover: "The_Influence_of_Contour_on_Similarity_Perception_of_Star_Glyphs.png",
    purpose: "Test how contour, fill, and reference structures influence similarity judgments for star glyphs.",
    method: "Three experiments compared experts, trained novices, and online participants using target-plus-alternative similarity-selection tasks.",
    finding: "Simple star glyphs without contours best supported data similarity; contours could shift attention toward overall shape instead.",
    relevance: "Justifies contour and enclosure features while showing that similarity is task-dependent and cannot be reduced to one universal distance.",
    note: "Experiment 1 included 12 novices and 12 experts; Experiment 2 retained 36 online participants after controls.",
    source: "papers/The_Influence_of_Contour_on_Similarity_Perception_of_Star_Glyphs.pdf, pp. 1–11",
  },
  {
    shortTitle: "Glyph evaluation is strongly task-dependent",
    citation: "Fuchs, Isenberg, Bezerianos & Keim · 2017",
    cover: "A_Systematic_Review_of_Experimental_Studies_on_Data_Glyphs.png",
    purpose: "Organize what controlled glyph studies tested, which tasks they used, and what design conclusions can be drawn.",
    method: "A systematic review and meta-analysis of 64 quantitative controlled user-study papers spanning roughly six decades.",
    finding: "Glyph performance depends on design, task, presentation setting, and data; the review identifies evidence patterns and open research gaps.",
    relevance: "Supports a quantitative human study and helps separate identification, similarity, confusability, accuracy, and response time as different outcomes.",
    note: "Use this paper to justify the study-design layer rather than an individual image-feature formula.",
    source: "papers/A_Systematic_Review_of_Experimental_Studies_on_Data_Glyphs.pdf, pp. 1–17",
  },
];

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
    addText(slide, "[THESIS TITLE]", { left: 42, top: 205, width: 1080, height: 125 }, {
      fontSize: 72,
      bold: true,
      verticalAlignment: "bottom",
    });
    addRect(slide, { left: 42, top: 371, width: 188, height: 5 }, C.accentLight);
    addText(slide, "Research problem, questions, and literature review", { left: 42, top: 414, width: 760, height: 65 }, {
      fontSize: 30,
    });
    addText(slide, "Name · Programme · Supervisor · Date", { left: 42, top: 588, width: 760, height: 28 }, {
      fontSize: 18,
      color: C.muted,
    });
    setSources(slide, [], ["Replace the title and identity line when the final thesis wording is confirmed."]);
  }

  // 2. Problem — Codex Grid slide-08 split silhouette.
  {
    const slide = presentation.slides.add();
    slide.background.fill = C.white;
    addSlideChrome(slide, "01 · THE PROBLEM", 2);
    addTitle(slide, "Visual similarity creates a practical comparison problem", 78, 110, 45);
    addText(slide,
      "Large icon collections contain repeated shapes, subtle variations, and icons that may become difficult to distinguish. Manual inspection cannot consistently explain which visible properties make two icons appear close or different.",
      { left: 42, top: 224, width: 510, height: 172 },
      { fontSize: 25 });
    addText(slide,
      "The thesis therefore needs an auditable bridge between visible pixels and later human judgments—without confusing visual similarity with semantic meaning.",
      { left: 42, top: 438, width: 510, height: 130 },
      { fontSize: 22, color: C.muted });
    addRect(slide, { left: 610, top: 176, width: 628, height: 452 }, C.panel, C.rule, 1);
    await addImage(slide, path.join(ROOT, "icon_data/analysis/similarity/closest_cross_set_pairs_euclidean.png"),
      { left: 626, top: 191, width: 596, height: 423 },
      { alt: "Closest cross-set feature-similar icon pairs", fit: "cover", crop: { left: 0, top: 0, right: 0, bottom: 0.36 } });
    setSources(slide, [
      "wiki/thesis-overview.md",
      "icon_data/analysis/similarity/closest_cross_set_pairs_euclidean.png",
    ]);
  }

  // 3. Research aim and questions — Codex Grid slide-09 / slide-17 sequence silhouette.
  {
    const slide = presentation.slides.add();
    slide.background.fill = C.white;
    addSlideChrome(slide, "02–03 · AIM AND RESEARCH QUESTIONS", 3);
    addTitle(slide, "The study connects computer measurements with human responses", 78, 84, 44);
    addText(slide,
      "Working aim: organize literature-supported visible icon properties into measurable feature families, then test where those measurements agree—or disagree—with human identification and perception.",
      { left: 42, top: 171, width: 1138, height: 83 },
      { fontSize: 23, color: C.muted });

    const questions = [
      ["RQ1", "Which visible properties can be measured consistently from normalized icon images?"],
      ["RQ2", "How can those measurements describe similarity, distance, and potential confusability?"],
      ["RQ3", "How well do computer-side measurements correspond to human identification and similarity judgments?"],
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

  // 4. Literature map — Codex Grid slide-15 topic map silhouette.
  {
    const slide = presentation.slides.add();
    slide.background.fill = C.white;
    addSlideChrome(slide, "04 · LITERATURE REVIEW", 4);
    addTitle(slide, "Seven papers define four parts of the thesis", 78, 76, 44);
    addText(slide,
      "The literature does not provide one complete model. Instead, it contributes complementary evidence for measurement, perceptual design, distinguishability, and evaluation.",
      { left: 42, top: 162, width: 1120, height: 70 },
      { fontSize: 22, color: C.muted });

    const groups = [
      ["MEASUREMENT", "Forsythe · Garcia", "Complexity, structure, abstractness, and the boundary between pixels and context."],
      ["VISUAL FOUNDATIONS", "Borgo et al.", "Visual channels, Gestalt organization, and task-dependent glyph design."],
      ["DISTINGUISHABILITY", "Legg et al. · Fuchs et al. (contour)", "Distance across channels, contour, closure, and similarity strategy."],
      ["DESIGN & EVALUATION", "Maguire et al. · Fuchs et al. (review)", "Systematic glyph design and evidence-based user-study planning."],
    ];
    groups.forEach(([label, names, body], index) => {
      const top = 270 + index * 89;
      addText(slide, label, { left: 42, top, width: 236, height: 23 }, {
        fontSize: 15,
        bold: true,
        color: C.accent,
      });
      addText(slide, names, { left: 292, top: top - 2, width: 380, height: 30 }, {
        fontSize: 21,
        bold: true,
      });
      addText(slide, body, { left: 700, top: top - 3, width: 500, height: 47 }, {
        fontSize: 18,
        color: C.muted,
      });
      if (index < groups.length - 1) addRect(slide, { left: 42, top: top + 60, width: 1196, height: 1 }, C.rule);
    });
    setSources(slide, ["wiki/literature-and-evidence.md", "notes/paper_feature_review.md", "papers/extracted_text/README.md"]);
  }

  let page = 5;
  for (const [index, paper] of papers.entries()) {
    await addPaperSlide(presentation, paper, page, index % 2 === 0);
    page += 1;
  }

  for (const [index, slide] of presentation.slides.items.entries()) {
    const stem = `slide-${String(index + 1).padStart(2, "0")}`;
    const png = await presentation.export({ slide, format: "png", scale: 1.5 });
    await fs.writeFile(path.join(RENDER_DIR, `${stem}.png`), new Uint8Array(await png.arrayBuffer()));
    const layout = await slide.export({ format: "layout" });
    await fs.writeFile(path.join(RENDER_DIR, `${stem}.layout.json`), await layout.text());
  }

  const montage = await presentation.export({ format: "webp", montage: true, scale: 1 });
  await fs.writeFile(path.join(TMP, "deck-montage.webp"), new Uint8Array(await montage.arrayBuffer()));

  const pptx = await PresentationFile.exportPptx(presentation);
  await pptx.save(OUT);
  console.log(OUT);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
