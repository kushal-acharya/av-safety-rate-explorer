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


def _rewrite_input(directory, filename, mutate):
    """Simulate a reviewed/rehashed source update so semantic checks, not hashes, reject it."""
    import csv
    import hashlib

    path = directory / filename
    with path.open(newline="") as handle:
        reader = csv.DictReader(handle)
        fields, rows = reader.fieldnames, list(reader)
    mutate(rows)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    manifest_path = directory / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["processed_sha256"][filename] = hashlib.sha256(path.read_bytes()).hexdigest()
    manifest_path.write_text(json.dumps(manifest))


@pytest.mark.parametrize(
    "filename,column,value,error",
    [
        ("events.csv", "injury", "2", "membership must be 0 or 1"),
        ("events.csv", "airbag", "", "finite and nonnegative"),
        ("events.csv", "in_transport", "-1", "finite and nonnegative"),
        ("events.csv", "year_month", "202013", "invalid calendar month"),
        ("events.csv", "year_month", "202501", "frozen window"),
        ("events.csv", "source_row", "2.5", "integer values"),
        ("events.csv", "source_row", "0", "unique CSV row"),
        ("events.csv", "city", "UNKNOWN", "event city scope"),
        ("events.csv", "report_id", "30270.123", "malformed report_id"),
        ("cells.csv", "cell_id", "9.278157763509223e18", "19-digit"),
        ("cells.csv", "human_miles", "0", "must be positive"),
        ("cells.csv", "waymo_miles", "inf", "finite and nonnegative"),
        ("cells.csv", "benchmark_count", "-1", "finite and nonnegative"),
        ("city_inputs.csv", "baseline_ipmm", "nan", "finite and nonnegative"),
        ("city_inputs.csv", "published_matched_ipmm", "0", "must be positive"),
        ("city_inputs.csv", "published_events", "1.5", "integer values"),
        ("city_inputs.csv", "waymo_miles", "20000000", "city mileage must agree"),
    ],
)
def test_rehashed_invalid_fields_fail_before_computation(tmp_path, filename, column, value, error):
    directory = tmp_path / "geo"
    shutil.copytree(GEO_DIR, directory)
    _rewrite_input(directory, filename, lambda rows: rows[0].update({column: value}))
    with pytest.raises(ValueError, match=error):
        load_geography(directory)


def test_outcome_membership_requires_in_transport(tmp_path):
    directory = tmp_path / "geo"
    shutil.copytree(GEO_DIR, directory)
    _rewrite_input(
        directory, "events.csv", lambda rows: rows[0].update(injury="1", in_transport="0")
    )
    with pytest.raises(ValueError, match="outside in-transport"):
        load_geography(directory)


@pytest.mark.parametrize("index", [10, -1])
def test_deleted_source_row_is_not_silently_dropped(tmp_path, index):
    directory = tmp_path / "geo"
    shutil.copytree(GEO_DIR, directory)
    _rewrite_input(directory, "events.csv", lambda rows: rows.pop(index))
    with pytest.raises(ValueError, match="every consecutive source CSV row"):
        load_geography(directory)


def test_missing_outcome_for_cell_fails(tmp_path):
    directory = tmp_path / "geo"
    shutil.copytree(GEO_DIR, directory)
    _rewrite_input(directory, "cells.csv", lambda rows: rows.pop(0))
    with pytest.raises(ValueError, match="every selected outcome"):
        load_geography(directory)


def test_manifest_cannot_omit_input_hashes(tmp_path):
    directory = tmp_path / "geo"
    shutil.copytree(GEO_DIR, directory)
    path = directory / "manifest.json"
    manifest = json.loads(path.read_text())
    manifest["processed_sha256"].pop("events.csv")
    path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="exactly the three"):
        load_geography(directory)


def test_added_non_outcome_row_cannot_expand_frozen_cohort(tmp_path):
    directory = tmp_path / "geo"
    shutil.copytree(GEO_DIR, directory)
    _rewrite_input(
        directory,
        "events.csv",
        lambda rows: rows.append({**rows[0], "source_row": "525", "injury": "0", "airbag": "0"}),
    )
    with pytest.raises(ValueError, match="523 expected"):
        load_geography(directory)
