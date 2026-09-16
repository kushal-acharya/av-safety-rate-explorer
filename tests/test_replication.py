"""Published references, independent distribution identities, and cohort provenance."""

import json
import math
import shutil

import pytest
from scipy.stats import beta

from av_safety.replication import (
    ROOT,
    STUDY_DIR,
    load_study_inputs,
    nelson_interval,
    reproduce_study,
)


def test_reproduces_four_published_reference_cases():
    study = reproduce_study()
    assert study["audit"] == {
        "listed_events": 73,
        "in_transport_impacted": 63,
        "any_injury": 4,
        "police_reported": 15,
        "pre_sgo_events": 2,
        "checks_passed": 16,
        "checks_total": 16,
    }
    primary = study["comparisons"][0]
    assert primary["event_ids"] == ["30270-6336"]
    assert primary["paper_code"]["ratio"] == pytest.approx(1 / (1.755 * 5.82))
    assert primary["paper_code"]["upper"] == pytest.approx(0.62, abs=0.01)
    assert primary["cohort"] == {
        "listed": 34,
        "in_transport_impacted": 29,
        "excluded_transport_or_contact": 5,
        "excluded_outcome": 28,
        "included": 1,
    }


def test_equation_agrees_with_transformed_binomial_interval():
    # Integer benchmark count: independently transform a beta/binomial interval.
    result = nelson_interval(5, 2e6, 10, 3e6)
    lower = beta.ppf(0.025, 5, 31)
    upper = beta.ppf(0.975, 6, 30)
    assert result["lower"] == pytest.approx(1.5 * lower / (1 - lower))
    assert result["upper"] == pytest.approx(1.5 * upper / (1 - upper))


def test_paper_code_tail_difference_is_visible_and_material():
    row = reproduce_study()["comparisons"][1]  # Phoenix injury reference
    assert row["paper_code"]["tail_probability"] == 0.0125
    assert row["equation"]["tail_probability"] == 0.025
    assert row["paper_code"]["lower"] < row["equation"]["lower"]
    assert row["paper_code"]["upper"] > 1 > row["equation"]["upper"]


def test_zero_count_has_finite_upper_bound_no_pseudo_events():
    result = nelson_interval(0, 1e6, 2, 100e6)
    assert result["ratio"] == result["lower"] == 0
    # For Y=0, the beta-prime (1,X) quantile has a closed form.
    assert result["upper"] == pytest.approx(100 * math.expm1(-math.log(0.025) / 200))
    assert result == nelson_interval(0, 1e6, 2, 100e6, convention="paper_code")


@pytest.mark.parametrize(
    "args",
    [(-1, 1, 1, 1), (1.5, 1, 1, 1), (1, 0, 1, 1), (1, 1, 0, 1), (1, 1, 1, -1), (1, math.nan, 1, 1)],
)
def test_invalid_replication_inputs(args):
    with pytest.raises(ValueError):
        nelson_interval(*args)


def test_frozen_inputs_fail_closed_on_changes(tmp_path):
    for name in ["manifest.json", "events.csv", "comparisons.csv"]:
        shutil.copy(STUDY_DIR / name, tmp_path / name)
    with (tmp_path / "events.csv").open("a") as output:
        output.write("unexpected source edit\n")
    with pytest.raises(ValueError, match="hash mismatch"):
        load_study_inputs(tmp_path)


def test_browser_artifact_equals_fresh_calculation():
    frozen = json.loads((ROOT / "web/waymo-project/replication.json").read_text())
    assert reproduce_study() == frozen
