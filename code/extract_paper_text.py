#!/usr/bin/env python3
"""Extract paper PDF text into stable text files and a manifest."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path

import pdfplumber


ROOT = Path(__file__).resolve().parents[1]
PAPERS_DIR = ROOT / "papers"
OUTPUT_DIR = PAPERS_DIR / "extracted_text"


def slugify(value: str) -> str:
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")


def clean_text(value: str) -> str:
    value = value.replace("\r\n", "\n").replace("\r", "\n")
    value = re.sub(r"[ \t]+\n", "\n", value)
    value = re.sub(r"\n{4,}", "\n\n\n", value)
    return value.strip()


def extract_pdf(path: Path, output_dir: Path) -> dict[str, object]:
    pages: list[str] = []
    metadata: dict[str, object] = {}
    with pdfplumber.open(path) as pdf:
        metadata = dict(pdf.metadata or {})
        for page_index, page in enumerate(pdf.pages, start=1):
            text = page.extract_text(x_tolerance=1, y_tolerance=3) or ""
            text = clean_text(text)
            pages.append(f"--- PAGE {page_index} ---\n{text}".rstrip())

    text_body = "\n\n".join(pages).strip() + "\n"
    slug = slugify(path.stem)
    output_path = output_dir / f"{slug}.txt"
    output_path.write_text(text_body, encoding="utf-8")

    return {
        "pdf": str(path.relative_to(ROOT)),
        "text": str(output_path.relative_to(ROOT)),
        "pages": len(pages),
        "characters": len(text_body),
        "pdf_metadata": metadata,
    }


def write_index(entries: list[dict[str, object]], output_dir: Path) -> None:
    lines = [
        "# Extracted Paper Text",
        "",
        "This folder contains page-marked text extracted from the thesis PDF papers.",
        "Regenerate with:",
        "",
        "```bash",
        "/Users/macbook/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 code/extract_paper_text.py",
        "```",
        "",
        "| Paper | Text file | Pages | Characters |",
        "|---|---:|---:|---:|",
    ]
    for entry in entries:
        lines.append(
            f"| `{entry['pdf']}` | `{entry['text']}` | {entry['pages']} | {entry['characters']} |"
        )
    (output_dir / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract reusable text from PDF papers.")
    parser.add_argument("--papers-dir", type=Path, default=PAPERS_DIR)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    pdfs = sorted(args.papers_dir.glob("*.pdf"))
    entries = [extract_pdf(path, args.output_dir) for path in pdfs]
    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "papers_dir": str(args.papers_dir.relative_to(ROOT)),
        "output_dir": str(args.output_dir.relative_to(ROOT)),
        "paper_count": len(entries),
        "papers": entries,
    }
    (args.output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    write_index(entries, args.output_dir)
    print(f"Extracted {len(entries)} PDFs to {args.output_dir}")


if __name__ == "__main__":
    main()
