"""Reproduce this nomination locally; never writes to Cloudflare."""
from pathlib import Path
import csv
import hashlib
import json
import sys

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "code"))
from thesis_pipeline.features.registry import ORIENTATION_CONFIDENCE_THRESHOLD


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    catalog_path = OUT / "catalog.json"
    catalog = json.loads(catalog_path.read_text())
    features_path = ROOT / "icon_data/analysis/features.csv"
    features = {r["icon_id"]: r for r in csv.DictReader(features_path.open(encoding="utf-8"))}
    ids = catalog["feature_ids"]
    scalar_ids = [f for f in ids if f != "principal_axis_orientation_v2"]
    payload = {"reviewer_code": "ibtisam", "selection_version": "five-sets-up-to-20-v2", "selections": {}}
    rows, summaries = [], []
    for source in catalog["sets"]:
        candidates, seen_images = [], set()
        exclusions = {"uncertain_mask": 0, "invalid_features": 0, "invisible_on_white": 0, "duplicate_image": 0}
        for icon in sorted(source["icons"], key=lambda x: x["icon_id"]):
            r = features[icon["icon_id"]]
            if r["mask_is_uncertain"].lower() != "false":
                exclusions["uncertain_mask"] += 1
                continue
            if not all(np.isfinite(float(r[f])) for f in ids):
                exclusions["invalid_features"] += 1
                continue
            with Image.open(ROOT / "icon_data" / icon["normalized_path"]) as image:
                image = image.convert("RGBA")
                assert image.size == (256, 256)
                on_white = Image.alpha_composite(Image.new("RGBA", image.size, "white"), image).convert("RGB")
                if int(np.count_nonzero(np.any(np.array(on_white) < 245, axis=2))) < 8:
                    exclusions["invisible_on_white"] += 1
                    continue
                pixel_hash = hashlib.sha256(image.tobytes()).hexdigest()
            if pixel_hash in seen_images:
                exclusions["duplicate_image"] += 1
                continue
            seen_images.add(pixel_hash)
            candidates.append((icon, r, pixel_hash))
        n = len(candidates)
        assert n >= 20, (source["set_id"], n)
        # Equal-weight scalar percentile distances; ties receive a common midrank.
        values = np.array([[float(r[f]) for f in scalar_ids] for _, r, _ in candidates])
        active = np.ptp(values, axis=0) > 1e-12
        ranks = np.zeros_like(values)
        for k in np.flatnonzero(active):
            v = values[:, k]
            ranks[:, k] = [(np.sum(v < x) + (np.sum(v == x) - 1) / 2) / (n - 1) for x in v]
        sums = np.sum((ranks[:, None, active] - ranks[None, :, active]) ** 2, axis=2)
        counts = np.full((n, n), int(active.sum()), dtype=float)
        angle = np.array([float(r["principal_axis_orientation_v2"]) for _, r, _ in candidates])
        defined = np.array([float(r["orientation_confidence_v2"]) >= ORIENTATION_CONFIDENCE_THRESHOLD for _, r, _ in candidates])
        both = defined[:, None] & defined[None, :]
        delta = np.abs(angle[:, None] - angle[None, :]) % np.pi
        axial = np.minimum(delta, np.pi - delta) / (np.pi / 2)
        sums += np.where(both, axial ** 2, 0)
        counts += both
        distances = np.sqrt(np.divide(sums, counts, out=np.zeros_like(sums), where=counts > 0))
        # Four disjoint close pairs, diversified across the measured space.
        pairs = [(i, j) for i in range(n) for j in range(i + 1, n)]
        cutoff = float(np.quantile([distances[i, j] for i, j in pairs], .25))
        close = [(i, j) for i, j in pairs if distances[i, j] <= cutoff]
        selected, reasons, partner = [], {}, {}
        for pair_number in range(1, 5):
            available = [(i, j) for i, j in close if i not in selected and j not in selected]
            assert available
            if not selected:
                i, j = min(available, key=lambda p: (distances[p], p))
            else:
                def pair_key(p):
                    novelty = min(np.min(distances[p[0], selected]), np.min(distances[p[1], selected]))
                    return (-float(novelty), float(distances[p]), p)
                i, j = min(available, key=pair_key)
            for a, b in [(i, j), (j, i)]:
                selected.append(a)
                reasons[a] = f"close_feature_pair_{pair_number}"
                partner[a] = b
        remaining = [i for i in range(n) if i not in selected]
        medoid = min(remaining, key=lambda i: (float(np.mean(distances[i])), i))
        selected.append(medoid)
        reasons[medoid] = "central_feature_example"
        while len(selected) < 20:
            remaining = [i for i in range(n) if i not in selected]
            chosen = min(remaining, key=lambda i: (-float(np.min(distances[i, selected])), i))
            selected.append(chosen)
            reasons[chosen] = "feature_space_coverage"
        payload["selections"][source["set_id"]] = [candidates[i][0]["icon_id"] for i in selected]
        for order, i in enumerate(selected, 1):
            icon, r, image_hash = candidates[i]
            rows.append({"set_id": source["set_id"], "selection_order": order, "icon_id": icon["icon_id"], "label": icon["label"], "reason": reasons[i], "pair_partner_icon_id": candidates[partner[i]][0]["icon_id"] if i in partner else "", "pair_distance": float(distances[i, partner[i]]) if i in partner else "", "orientation_defined": bool(defined[i]), "image_pixel_sha256": image_hash, **{f: float(r[f]) for f in ids}})
        summaries.append({"set_id": source["set_id"], "source_count": len(source["icons"]), "candidate_count": n, "exclusions": exclusions, "selected_count": 20, "defined_orientation_count": int(defined[selected].sum()), "close_pair_cutoff": cutoff, "coverage_radius": float(np.max(np.min(distances[:, selected], axis=1))), "scalar_feature_ranges": {f: {"pool_min": float(values[:, k].min()), "pool_max": float(values[:, k].max()), "selected_min": float(values[selected, k].min()), "selected_max": float(values[selected, k].max())} for k, f in enumerate(scalar_ids)}})
    assert len(rows) == 100 and len({r["icon_id"] for r in rows}) == 100
    (OUT / "submission.json").write_text(json.dumps(payload, indent=2) + "\n")
    with (OUT / "selection.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    (OUT / "method.json").write_text(json.dumps({"selection_kind": "algorithm-assisted research-group nomination; not an independent human rating", "features_sha256": digest(features_path), "catalog_sha256": digest(catalog_path), "orientation_confidence_threshold": ORIENTATION_CONFIDENCE_THRESHOLD, "distance": "RMS of equal-weight per-set scalar midrank percentile differences and axial angle differences/(pi/2); constant scalars omitted; orientation omitted pairwise if either confidence is low", "sampling": "4 disjoint pairs within lowest quartile of candidate distances, diversified by distance to previous choices; one remaining medoid; 11 greedy farthest-point additions", "tie_break": "ascending icon_id", "supervisor_choices_used": False, "human_visual_review_performed": False, "limitations": ["Measured closeness is not human confusability", "Technical mask checks do not establish measurement validity", "Not final consensus stimuli or pilot approval", "Pairwise omission of undefined orientation can compare different channel subsets"], "sets": summaries}, indent=2) + "\n")
    print(json.dumps(summaries, indent=2))


if __name__ == "__main__":
    main()
