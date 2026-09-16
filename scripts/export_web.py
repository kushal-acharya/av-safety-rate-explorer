"""Export source-derived aggregates and offline statsmodels NB fits for the web UI."""

from __future__ import annotations

import itertools
import json
import math

from av_safety.data import CONTEXT_CATEGORIES, ROOT, context_aggregates, load_processed
from av_safety.stats import dispersion_test, nb_rate_ci


def main() -> None:
    """Precompute per-manufacturer fits for every available year subset, once."""
    tables = load_processed()
    annual = tables["exposure"]
    units = tables["units"]
    fits = {}
    for (mode, manufacturer), group in units.groupby(["mode", "manufacturer"]):
        years = sorted(group.year.unique().tolist())
        for size in range(1, len(years) + 1):
            for subset in itertools.combinations(years, size):
                selected = group[group.year.isin(subset)]
                usable = selected[selected.miles > 0]
                if usable.empty:
                    continue
                diagnostic = dispersion_test(usable.reported_events, usable.miles)
                invalid = selected[(selected.miles == 0) & (selected.reported_events > 0)]
                if not invalid.empty:
                    fit = {
                        "method": "Poisson exact",
                        "warning": "A zero-mile vehicle has events; NB fit disabled.",
                    }
                else:
                    fit = nb_rate_ci(usable.reported_events, usable.miles).to_dict()
                    if fit["method"].startswith("Negative"):
                        fit["log_se"] = (math.log(fit["upper"]) - math.log(fit["lower"])) / (
                            2 * 1.95996398454
                        )
                fits[f"{mode}|{manufacturer}|{','.join(map(str, subset))}"] = {**fit, **diagnostic}
    context = context_aggregates(tables["events"])
    data = {
        "years": [2020, 2021, 2022, 2023, 2024],
        "retrieved": "2026-09-16",
        "annual": annual.to_dict("records"),
        "fits": fits,
        "context": {key: frame.to_dict("records") for key, frame in context.items()},
        "context_categories": CONTEXT_CATEGORIES,
        "audit": tables["audit"].to_dict("records"),
    }
    out = ROOT / "web/waymo-project"
    out.mkdir(parents=True, exist_ok=True)
    (out / "data.json").write_text(json.dumps(data, separators=(",", ":"), allow_nan=False))
    for name in ["exposure", "audit"]:
        (out / f"{name}.csv").write_bytes((ROOT / f"data/processed/{name}.csv").read_bytes())
    (out / "sources.json").write_bytes((ROOT / "data/source_manifest.json").read_bytes())
    print(f"Exported {len(fits)} audited fit combinations")


if __name__ == "__main__":
    main()
