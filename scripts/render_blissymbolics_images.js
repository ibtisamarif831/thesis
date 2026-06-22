#!/usr/bin/env node
const crypto = require("crypto");
const fs = require("fs");
const path = require("path");
const vm = require("vm");

const ROOT = path.resolve(__dirname, "..");
const BLISS_DIR = path.join(ROOT, "icon_data", "iconsets", "06_blissymbolics");
const CHAR_OUT = path.join(BLISS_DIR, "rendered_svg", "chars");
const WORD_OUT = path.join(BLISS_DIR, "rendered_svg", "words");
const META_DIR = path.join(BLISS_DIR, "metadata");
const META_PATH = path.join(META_DIR, "rendered_symbols.json");

const INLINE_STYLE = `<style>
.bliss-line,.bliss-disc,.bliss-dot{stroke:#000;stroke-linejoin:round;stroke-linecap:round;stroke-width:8}
.bliss-line{fill:none}
.bliss-disc,.bliss-dot{fill:#000}
.bliss-text{font-family:"Helvetica Neue",Helvetica,Arial,"Liberation Sans",sans-serif;fill:#000}
</style>`;

function loadBlissRuntime() {
  const context = {};
  vm.createContext(context);
  for (const filename of ["blissdata_chars.js", "blissdata_words.js", "blissviewer.js"]) {
    const source = fs.readFileSync(path.join(BLISS_DIR, filename), "utf8");
    vm.runInContext(source, context, { filename });
  }
  return {
    BlissViewer: context.BlissViewer,
    charData: context.BLISS_CHAR_DATA,
    wordData: context.BLISS_WORD_DATA,
  };
}

function labelFromId(id) {
  return id.split(",")[0].trim();
}

function filenameFor(id) {
  const label = labelFromId(id)
    .toLowerCase()
    .normalize("NFKD")
    .replace(/[^\w\s-]/g, "")
    .replace(/[_\s-]+/g, "_")
    .replace(/^_+|_+$/g, "")
    .slice(0, 80) || "symbol";
  const digest = crypto.createHash("sha1").update(id).digest("hex").slice(0, 12);
  return `${label}__${digest}.svg`;
}

function svgFor(viewer, id) {
  const expanded = viewer.expand_word(id);
  const margin = viewer.config.margin;
  let svg = viewer.format(viewer.SVG_START, {
    x: expanded.left - margin,
    y: expanded.top - margin,
    w: expanded.right - expanded.left + 2 * margin,
    h: expanded.bottom - expanded.top + 2 * margin,
  });
  svg = svg.replace("<g>", `${INLINE_STYLE}<g>`);
  svg += viewer.to_svg_obj(0, 0, expanded.chars);
  svg += viewer.SVG_END;
  return `${svg}\n`;
}

function cleanOutput(dir) {
  fs.mkdirSync(dir, { recursive: true });
  for (const entry of fs.readdirSync(dir)) {
    if (entry.toLowerCase().endsWith(".svg")) {
      fs.rmSync(path.join(dir, entry));
    }
  }
}

function renderGroup(viewer, ids, kind, outDir) {
  cleanOutput(outDir);
  const records = [];
  for (const id of ids.sort()) {
    const filename = filenameFor(id);
    const outputPath = path.join(outDir, filename);
    fs.writeFileSync(outputPath, svgFor(viewer, id));
    records.push({
      id,
      label: labelFromId(id),
      kind,
      file: path.relative(BLISS_DIR, outputPath).split(path.sep).join("/"),
    });
  }
  return records;
}

function main() {
  const { BlissViewer, charData, wordData } = loadBlissRuntime();
  const viewer = new BlissViewer(charData, wordData, { margin: 8, radius: 4 });

  const charRecords = renderGroup(viewer, Object.keys(charData.chars), "char", CHAR_OUT);
  const wordRecords = renderGroup(viewer, Object.keys(wordData.words), "word", WORD_OUT);

  fs.mkdirSync(META_DIR, { recursive: true });
  fs.writeFileSync(
    META_PATH,
    `${JSON.stringify(
      {
        generated: "2026-06-22",
        source: "https://github.com/blissymbolics/blissymbols",
        renderer: "scripts/render_blissymbolics_images.js",
        counts: {
          chars: charRecords.length,
          words: wordRecords.length,
          total: charRecords.length + wordRecords.length,
        },
        symbols: [...charRecords, ...wordRecords],
      },
      null,
      2
    )}\n`
  );

  console.log(`Rendered ${charRecords.length} chars`);
  console.log(`Rendered ${wordRecords.length} words`);
  console.log(`Rendered ${charRecords.length + wordRecords.length} total SVGs`);
}

main();
