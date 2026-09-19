"""Reject obviously unusable Taiwei review frames.

This is a technical tripwire, not an aesthetic score. It catches black/white
renders, flat frames, and the known waterfall failure mode where most of the
frame is a black cliff silhouette with a bright empty background.
"""
from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageStat

ROOT = Path("ci_artifacts/review")
rows = []
problems = []

for path in sorted(ROOT.glob("*.png")):
    im = Image.open(path).convert("L")
    hist = im.histogram()
    n = im.width * im.height

    def percentile(frac: float) -> int:
        target = min(n - 1, max(0, int(frac * n)))
        seen = 0
        for value, count in enumerate(hist):
            seen += count
            if seen > target:
                return value
        return 255

    stat = ImageStat.Stat(im)
    mean = stat.mean[0]
    stdev = stat.stddev[0]
    p01, p50, p99 = percentile(.01), percentile(.50), percentile(.99)
    row = {
        "file": path.name,
        "mean": round(mean, 2),
        "stdev": round(stdev, 2),
        "p01": p01,
        "p50": p50,
        "p99": p99,
    }
    rows.append(row)

    if mean < 8:
        problems.append(f"{path.name}: nearly black mean={mean:.1f}")
    if mean > 225:
        problems.append(f"{path.name}: nearly white mean={mean:.1f}")
    if stdev < 7:
        problems.append(f"{path.name}: flat stdev={stdev:.1f}")
    if "09_" in path.name and p50 < 12:
        problems.append(
            f"{path.name}: waterfall review dominated by occluding silhouette p50={p50}"
        )

report = {"shots": rows, "problems": problems}
(ROOT / "pixel_qa.json").write_text(
    json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
)
print(json.dumps(report, ensure_ascii=False, indent=2))
if problems:
    raise SystemExit(1)
