"""Generate independent SciPy reference vectors for the JavaScript estimators."""

from __future__ import annotations

import json

from av_safety.data import ROOT
from av_safety.stats import miles_needed, poisson_rate_ci, power_curve, rate_ratio_ci


def main() -> None:
    """Write deterministic cross-language reference values."""
    cases = [
        (k, m, a)
        for k in [0, 1, 5, 50, 244, 1000, 10000]
        for m in [0.01, 1000, 1e8]
        for a in [0.1, 0.05, 0.01]
    ]
    ratios = [
        (0, 1000, 0, 2000),
        (5, 1000, 0, 1000),
        (0, 2000, 20, 1000),
        (20, 1000, 40, 2000),
        (244, 2389565.2, 212, 3669962.4),
        (1000, 5000, 1800, 9000),
    ]
    planners = [
        (r, d, a, p, phi, f, side)
        for r in [0.000001, 0.001, 1]
        for d in [0.01, 0.1, 0.5]
        for a, p, phi, f, side in [
            (0.05, 0.8, 1, 0.5, True),
            (0.01, 0.95, 5, 0.3, True),
            (0.1, 0.9, 2, 0.7, False),
        ]
    ]
    out = {
        "poisson": [{"args": c, "result": poisson_rate_ci(*c).to_dict()} for c in cases],
        "ratio": [{"args": c, "result": rate_ratio_ci(*c)} for c in ratios],
        "plan": [{"args": c, "result": miles_needed(*c)} for c in planners],
        "power": [
            {
                "args": [1e6, 0.001, 0.1, 0.05, 1, 0.5, True],
                "result": float(power_curve(0.001, 0.1, [1e6])[0]),
            }
        ],
    }
    (ROOT / "tests/reference.json").write_text(json.dumps(out, indent=2) + "\n")


if __name__ == "__main__":
    main()
