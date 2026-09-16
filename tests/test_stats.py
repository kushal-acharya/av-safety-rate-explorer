"""Reference numbers, boundary behavior and nontrivial planning invariants."""

import math

import numpy as np
import pytest

from av_safety.stats import (
    dispersion_test,
    miles_needed,
    nb_rate_ci,
    poisson_rate_ci,
    power_curve,
    rate_ratio_ci,
    rule_of_three,
)


def test_garwood_reference():
    zero = poisson_rate_ci(0, 1000)
    assert zero.lower == 0
    assert zero.upper == pytest.approx(-math.log(0.025) / 1000)
    five = poisson_rate_ci(5, 1)
    assert five.lower == pytest.approx(1.623486, abs=1e-6)
    assert five.upper == pytest.approx(11.668332, abs=1e-6)
    assert rule_of_three(1000) == pytest.approx(2.99573227355 / 1000)


@pytest.mark.parametrize("miles", [0.001, 1, 1e12])
def test_exposure_scaling(miles):
    r = poisson_rate_ci(5, miles)
    assert r.rate * miles == 5
    assert r.lower < r.rate < r.upper


def test_ratio_and_zero_counts():
    r = rate_ratio_ci(20, 1000, 40, 2000)
    assert r["ratio"] == 1
    assert r["lower"] < 1 < r["upper"]
    assert r["p"] == pytest.approx(1)
    z = rate_ratio_ci(5, 1000, 0, 1000)
    assert z["ratio"] == 0 and z["upper"] > 0
    assert rate_ratio_ci(0, 1000, 0, 1000)["ratio"] is None


def test_planner_hand_calculation_and_power():
    # z(.975)=1.959963985, z(.8)=.841621234; T=(sum z)^2*.0038/(.0001)^2.
    result = miles_needed(0.001, 0.1)
    assert result["total_miles"] == pytest.approx(2_982_574.299, abs=0.01)
    assert result["events_a"] == pytest.approx(1491.28715, abs=0.001)
    assert power_curve(0.001, 0.1, [result["total_miles"]])[0] == pytest.approx(0.8, abs=1e-5)
    assert miles_needed(0.001, 0.2)["total_miles"] < result["total_miles"]
    assert miles_needed(0.001, 0.1, power=0.9)["total_miles"] > result["total_miles"]
    assert miles_needed(0.001, 0.1, dispersion=2)["total_miles"] == 2 * result["total_miles"]
    assert np.all(np.diff(power_curve(0.001, 0.1, np.linspace(0, 1e7, 100))) >= 0)


def test_nb_overdispersion_and_fallback():
    k = [0, 1, 2, 40, 60, 0, 3, 80, 2, 20]
    m = [1000] * len(k)
    nb = nb_rate_ci(k, m)
    p = poisson_rate_ci(sum(k), sum(m))
    assert dispersion_test(k, m)["overdispersed"]
    assert nb.method.startswith("Negative binomial")
    assert nb.lower < p.lower < p.upper < nb.upper
    assert nb_rate_ci([1, 2], [10, 10]).warning
    assert nb_rate_ci([0, 0, 0], [10, 10, 10]).method == "Poisson exact"


@pytest.mark.parametrize(
    "call",
    [
        lambda: poisson_rate_ci(-1, 1),
        lambda: poisson_rate_ci(1.2, 1),
        lambda: poisson_rate_ci(1, 0),
        lambda: poisson_rate_ci(1, 1, alpha=1),
        lambda: rule_of_three(-1),
        lambda: rule_of_three(1, conf=1),
        lambda: nb_rate_ci([-1], [1]),
        lambda: dispersion_test([1], [-1]),
        lambda: dispersion_test([], []),
        lambda: dispersion_test([1], [1, 2]),
        lambda: rate_ratio_ci(1, 0, 2, 1),
        lambda: miles_needed(-1, 0.1),
        lambda: miles_needed(0.001, 0),
        lambda: miles_needed(0.001, 0.1, dispersion=0.5),
        lambda: miles_needed(0.001, 0.1, allocation=1),
        lambda: power_curve(0.001, 0.1, [-1]),
        lambda: poisson_rate_ci(1, math.inf),
    ],
)
def test_input_validation(call):
    with pytest.raises(ValueError):
        call()
