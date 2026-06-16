#!/usr/bin/env python3
"""Create visual reports from extracted icon feature CSVs."""

import argparse
import html
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler


ROOT = Path(__file__).resolve().parents[1]
FEATURES_CSV = ROOT / "icon_data/analysis/features.csv"
OUTPUT_DIR = ROOT / "icon_data/analysis/visualizations"

FEATURE_COLUMNS = [
    "foreground_area_ratio",
    "canny_edge_density",
    "connected_components",
    "quadtree_leaf_count",
    "quadtree_structural_variability",
    "quadtree_mean_leaf_size",
]

CHART_FEATURES = [
    "foreground_area_ratio",
    "canny_edge_density",
    "connected_components",
    "quadtree_structural_variability",
]


def load_features(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    for column in FEATURE_COLUMNS:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    return frame.dropna(subset=FEATURE_COLUMNS).reset_index(drop=True)


def write_summary(frame: pd.DataFrame, output_dir: Path) -> Path:
    summary = (
        frame.groupby(["set_id", "set_name"])[FEATURE_COLUMNS]
        .agg(["count", "mean", "median", "std", "min", "max"])
        .round(6)
    )
    summary.columns = [f"{feature}_{stat}" for feature, stat in summary.columns]
    output = output_dir / "feature_summary_by_set.csv"
    summary.to_csv(output)
    return output


def plot_feature_distributions(frame: pd.DataFrame, output_dir: Path) -> Path:
    set_names = sorted(frame["set_name"].unique())
    fig, axes = plt.subplots(len(CHART_FEATURES), 1, figsize=(15, 14), constrained_layout=True)

    for axis, feature in zip(axes, CHART_FEATURES):
        data = [frame.loc[frame["set_name"] == set_name, feature].to_numpy() for set_name in set_names]
        axis.boxplot(data, tick_labels=set_names, showfliers=False)
        axis.set_title(title_for(feature))
        axis.set_ylabel(feature)
        axis.tick_params(axis="x", labelrotation=35, labelsize=8)
        axis.grid(axis="y", alpha=0.25)

    output = output_dir / "feature_distributions_by_set.png"
    fig.savefig(output, dpi=180)
    plt.close(fig)
    return output


def plot_correlation_heatmap(frame: pd.DataFrame, output_dir: Path) -> Path:
    corr = frame[FEATURE_COLUMNS].corr(method="spearman")
    fig, axis = plt.subplots(figsize=(9, 7), constrained_layout=True)
    image = axis.imshow(corr, cmap="coolwarm", vmin=-1, vmax=1)
    axis.set_xticks(range(len(FEATURE_COLUMNS)), labels=FEATURE_COLUMNS, rotation=35, ha="right")
    axis.set_yticks(range(len(FEATURE_COLUMNS)), labels=FEATURE_COLUMNS)
    for row in range(len(FEATURE_COLUMNS)):
        for col in range(len(FEATURE_COLUMNS)):
            axis.text(col, row, f"{corr.iloc[row, col]:.2f}", ha="center", va="center", fontsize=8)
    axis.set_title("Spearman Feature Correlation")
    fig.colorbar(image, ax=axis, shrink=0.8)
    output = output_dir / "feature_correlation_heatmap.png"
    fig.savefig(output, dpi=180)
    plt.close(fig)
    return output


def plot_pca_scatter(frame: pd.DataFrame, output_dir: Path) -> Path:
    values = StandardScaler().fit_transform(frame[FEATURE_COLUMNS].to_numpy())
    coords = PCA(n_components=2, random_state=0).fit_transform(values)
    plot_frame = frame.copy()
    plot_frame["pc1"] = coords[:, 0]
    plot_frame["pc2"] = coords[:, 1]

    set_names = sorted(plot_frame["set_name"].unique())
    colors = plt.get_cmap("tab20")(np.linspace(0, 1, len(set_names)))

    fig, axis = plt.subplots(figsize=(12, 9), constrained_layout=True)
    for color, set_name in zip(colors, set_names):
        subset = plot_frame[plot_frame["set_name"] == set_name]
        axis.scatter(subset["pc1"], subset["pc2"], s=24, alpha=0.75, label=set_name, color=color)

    axis.set_title("PCA Projection of Icon Feature Vectors")
    axis.set_xlabel("PC1")
    axis.set_ylabel("PC2")
    axis.grid(alpha=0.2)
    axis.legend(loc="center left", bbox_to_anchor=(1, 0.5), fontsize=8)

    output = output_dir / "pca_feature_scatter_by_set.png"
    fig.savefig(output, dpi=180)
    plt.close(fig)
    return output


def create_set_contact_sheet(frame: pd.DataFrame, output_dir: Path, per_set: int = 12) -> Path:
    rows = []
    for _, subset in frame.groupby("set_name", sort=True):
        rows.extend(subset.sort_values("icon_id").head(per_set).to_dict("records"))
    output = output_dir / "sample_icons_by_set.png"
    make_contact_sheet(rows, output, columns=12, thumb_size=80, label_key="set_name")
    return output


def create_feature_extreme_sheets(frame: pd.DataFrame, output_dir: Path, per_side: int = 12) -> list[Path]:
    outputs = []
    for feature in CHART_FEATURES:
        low = frame.sort_values(feature, ascending=True).head(per_side).copy()
        high = frame.sort_values(feature, ascending=False).head(per_side).copy()
        low["extreme_label"] = "low " + feature
        high["extreme_label"] = "high " + feature
        rows = pd.concat([low, high], ignore_index=True).to_dict("records")
        output = output_dir / f"extremes_{feature}.png"
        make_contact_sheet(rows, output, columns=12, thumb_size=92, label_key="extreme_label", value_key=feature)
        outputs.append(output)
    return outputs


def make_contact_sheet(
    rows: list[dict],
    output: Path,
    columns: int,
    thumb_size: int,
    label_key: str,
    value_key: str | None = None,
) -> None:
    padding = 12
    label_height = 46 if value_key else 36
    cell_width = thumb_size + padding * 2
    cell_height = thumb_size + label_height + padding * 2
    row_count = math.ceil(len(rows) / columns)
    sheet = Image.new("RGB", (columns * cell_width, row_count * cell_height), "white")
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()

    for index, row in enumerate(rows):
        x = (index % columns) * cell_width
        y = (index // columns) * cell_height
        image_path = ROOT / row["normalized_path"]
        try:
            icon = Image.open(image_path).convert("RGBA")
        except Exception:
            icon = Image.new("RGBA", (thumb_size, thumb_size), (255, 255, 255, 0))
        icon.thumbnail((thumb_size, thumb_size), Image.Resampling.LANCZOS)
        icon_bg = Image.new("RGBA", (thumb_size, thumb_size), "white")
        icon_bg.alpha_composite(icon, ((thumb_size - icon.width) // 2, (thumb_size - icon.height) // 2))
        sheet.paste(icon_bg.convert("RGB"), (x + padding, y + padding))

        label = str(row.get(label_key, ""))[:24]
        draw.text((x + padding, y + padding + thumb_size + 4), label, fill=(30, 30, 30), font=font)
        if value_key:
            draw.text(
                (x + padding, y + padding + thumb_size + 18),
                f"{value_key}: {float(row[value_key]):.4f}",
                fill=(80, 80, 80),
                font=font,
            )

    sheet.save(output)


def write_html_report(
    outputs: list[Path],
    summary_csv: Path,
    frame: pd.DataFrame,
    input_features: Path,
    output_dir: Path,
) -> Path:
    rows_by_set = frame["set_name"].value_counts().sort_index()
    set_list = "\n".join(f"<li>{html.escape(name)}: {count}</li>" for name, count in rows_by_set.items())
    image_blocks = "\n".join(
        f'<section><h2>{html.escape(path.stem.replace("_", " ").title())}</h2>'
        f'<img src="{html.escape(path.name)}" alt="{html.escape(path.stem)}"></section>'
        for path in outputs
    )
    report = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Icon Feature Visual Report</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, sans-serif; margin: 32px; color: #222; }}
    img {{ max-width: 100%; border: 1px solid #ddd; }}
    section {{ margin: 32px 0; }}
    code {{ background: #f5f5f5; padding: 2px 4px; }}
  </style>
</head>
<body>
  <h1>Icon Feature Visual Report</h1>
  <p>Input: <code>{html.escape(relative_label(input_features))}</code></p>
  <p>Rows: {len(frame)}. Summary CSV: <a href="{html.escape(summary_csv.name)}">{html.escape(summary_csv.name)}</a>.</p>
  <h2>Rows By Icon Set</h2>
  <ul>{set_list}</ul>
  {image_blocks}
</body>
</html>
"""
    output = output_dir / "index.html"
    output.write_text(report, encoding="utf-8")
    return output


def title_for(feature: str) -> str:
    return feature.replace("_", " ").title()


def relative_label(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create visual reports from icon feature CSVs.")
    parser.add_argument("--features", type=Path, default=FEATURES_CSV)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    frame = load_features(args.features)

    outputs = []
    summary_csv = write_summary(frame, args.output_dir)
    outputs.append(plot_feature_distributions(frame, args.output_dir))
    outputs.append(plot_correlation_heatmap(frame, args.output_dir))
    outputs.append(plot_pca_scatter(frame, args.output_dir))
    outputs.append(create_set_contact_sheet(frame, args.output_dir))
    outputs.extend(create_feature_extreme_sheets(frame, args.output_dir))
    html_report = write_html_report(outputs, summary_csv, frame, args.features, args.output_dir)

    print(f"Wrote visual report to {html_report}")
    for output in [summary_csv, *outputs]:
        print(output)


if __name__ == "__main__":
    main()
