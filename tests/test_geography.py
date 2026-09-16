"""Spatial reweighting invariants, provenance, and frozen benchmark checks."""

import json
import math
import shutil

import pytest

from av_safety.geography import (
    GEO_DIR,
    ROOT,
    build_geography,
    load_geography,
    scenario,
    spatial_factor,
)


def test_hand_calculated_reweighting():
    assert spatial_factor([10, 30], [100, 100], [180, 20]) == pytest.approx(0.6)
    assert spatial_factor([10, 30], [100, 100], [100, 100]) == pytest.approx(1)
    assert spatial_factor([30, 10], [100, 100], [20, 180]) == pytest.approx(0.6)
    assert spatial_factor([100, 300], [1000, 1000], [180, 20]) == pytest.approx(0.6)


@pytest.mark.parametrize(
    "counts,human,av",
    [
        ([], [], []),
        ([1], [1, 2], [1]),
        ([1], [0], [1]),
        ([1], [-1], [1]),
        ([math.nan], [1], [1]),
        ([1], [math.inf], [1]),
        ([-1], [1], [1]),
        ([1], [1], [-1]),
        ([0], [1], [1]),
        ([1], [1], [0]),
    ],
)
def test_invalid_cell_vectors(counts, human, av):
    with pytest.raises(ValueError):
        spatial_factor(counts, human, av)


def test_frozen_reproduction_and_coverage():
    study = build_geography()
    assert study == json.loads((ROOT / "web/waymo-project/geography.json").read_text())
    assert study["audit"] == dict(
        unique_cells=987,
        cell_outcome_rows=2961,
        source_event_rows=523,
        benchmark_checks=9,
        count_checks=9,
    )
    for row in study["comparisons"]:
        assert abs(row["benchmark_delta"]) < 1e-9
        assert 0.996 < row["coverage"] < 1
        assert row["cell_miles"] + row["unallocated_miles"] == pytest.approx(row["waymo_miles"])
        assert sum(b["cells"] for b in row["bands"]) == row["cells"]
        for share in ["human_share", "waymo_share"]:
            assert sum(b[share] for b in row["bands"]) == pytest.approx(1)
        a, b = scenario(row, 0), scenario(row, 1)
        assert a["benchmark_ipmm"] == row["baseline_ipmm"]
        assert b["benchmark_ipmm"] == pytest.approx(row["matched_ipmm"])
        assert scenario(row, 0.5)["benchmark_ipmm"] == pytest.approx(
            (a["benchmark_ipmm"] + b["benchmark_ipmm"]) / 2
        )
        for field in ["ratio", "ratio_lower", "ratio_upper"]:
            assert scenario(row, 1, 0.5)[field] == pytest.approx(2 * b[field])
        for mix, stress in [(-0.1, 1), (1.1, 1), (math.nan, 1), (1, 0), (1, math.inf)]:
            with pytest.raises(ValueError):
                scenario(row, mix, stress)


def test_source_rows_and_cell_identifiers_preserved():
    cells, _, events, _ = load_geography()
    assert cells.cell_id.map(lambda x: isinstance(x, str) and len(x) == 19).all()
    assert (events.report_id == "").sum() == 2
    assert len(events[events.report_id == "30270-9540"]) == 2
    assert not events.source_row.duplicated().any()
    assert events.airbag.sum() == 15  # Includes Austin, which lacks cell data.


def test_hash_drift_fails_closed(tmp_path):
    shutil.copytree(GEO_DIR, tmp_path / "geo")
    with (tmp_path / "geo/cells.csv").open("a") as handle:
        handle.write("\n")
    with pytest.raises(ValueError, match="hash mismatch"):
        load_geography(tmp_path / "geo")
