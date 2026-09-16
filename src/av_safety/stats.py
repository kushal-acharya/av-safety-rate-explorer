"""Pure rare-event estimators. Rates are per mile; no UI or data dependencies."""

from __future__ import annotations

import math
import warnings
from collections.abc import Sequence
from dataclasses import asdict, dataclass

import numpy as np
from scipy.stats import binomtest, chi2, norm
from statsmodels.discrete.discrete_model import NegativeBinomial


@dataclass(frozen=True)
class Rate:
    """A rate and confidence interval, with an explicit estimation method."""

    rate: float
    lower: float
    upper: float
    method: str = "Poisson exact"
    dispersion: float = 0.0
    warning: str = ""

    def to_dict(self) -> dict:
        """Return a JSON-serializable result."""
        return asdict(self)


def _prob(value: float, name: str) -> None:
    if not math.isfinite(value) or not 0 < value < 1:
        raise ValueError(f"{name} must be strictly between 0 and 1")


def _validate(events: float, miles: float, alpha: float = 0.05) -> None:
    _prob(alpha, "alpha")
    if not math.isfinite(events) or events < 0 or int(events) != events:
        raise ValueError("events must be a nonnegative integer")
    if not math.isfinite(miles) or miles <= 0:
        raise ValueError("miles must be positive and finite")


def poisson_rate_ci(events: int, miles: float, alpha: float = 0.05) -> Rate:
    """Return the Garwood (1936) exact two-sided Poisson rate interval.

    Args: events is an integer count; miles is positive exposure; alpha is tail mass.
    Returns: Rate in events per mile. UI must show bounds, not zero risk, for k=0.
    Formula: [chi2(alpha/2, 2k), chi2(1-alpha/2, 2k+2)] / (2*miles).
    """
    _validate(events, miles, alpha)
    lower = 0.0 if events == 0 else chi2.ppf(alpha / 2, 2 * events) / (2 * miles)
    upper = chi2.ppf(1 - alpha / 2, 2 * events + 2) / (2 * miles)
    return Rate(events / miles, float(lower), float(upper))


def rule_of_three(miles: float, conf: float = 0.95) -> float:
    """Return the exact one-sided zero-count upper bound, -log(1-conf)/miles.

    Args: positive miles and confidence in (0,1). Returns: upper rate per mile.
    Reference: Poisson P(K=0)=exp(-rate*miles); 95% coefficient is 2.995732.
    """
    _prob(conf, "confidence")
    _validate(0, miles)
    return -math.log1p(-conf) / miles


def _units(events: Sequence[float], miles: Sequence[float]) -> tuple:
    k, m = np.asarray(events, dtype=float), np.asarray(miles, dtype=float)
    if k.ndim != 1 or m.ndim != 1 or len(k) == 0 or len(k) != len(m):
        raise ValueError("event and exposure vectors must be nonempty, aligned, and 1-D")
    for count, exposure in zip(k, m, strict=True):
        _validate(count, exposure)
    return k, m


def dispersion_test(events_by_unit: Sequence[float], miles_by_unit: Sequence[float]) -> dict:
    """Return Pearson dispersion and an asymptotic chi-square diagnostic.

    Args: aligned counts and positive exposures. Returns: phi, p, units, overdispersed.
    Formula: X2=sum((k-mu)^2/mu); phi=X2/(n-1), mu=miles*sum(k)/sum(miles).
    Reference: McCullagh & Nelder (1989), GLM Pearson statistic. Sparse counts
    weaken the chi-square calibration; this diagnostic does not prove independence.
    """
    k, m = _units(events_by_unit, miles_by_unit)
    if len(k) < 2 or k.sum() == 0:
        return {"phi": 1.0, "p": 1.0, "units": len(k), "overdispersed": False}
    mu = m * k.sum() / m.sum()
    statistic = float(np.sum((k - mu) ** 2 / mu))
    phi = statistic / (len(k) - 1)
    p = float(chi2.sf(statistic, len(k) - 1))
    return {"phi": phi, "p": p, "units": len(k), "overdispersed": phi > 1 and p < 0.05}


def nb_rate_ci(
    events_by_unit: Sequence[float], miles_by_unit: Sequence[float], alpha: float = 0.05
) -> Rate:
    """Fit intercept-only NB2 with log(exposure) offset; estimate alpha by ML.

    Args: unit counts, positive miles, tail mass. Returns: log-Wald rate CI and NB alpha.
    Formula: E[K_i]=m_i*exp(b); Var(K_i)=mu_i+a*mu_i^2; CI=exp(b +/- z*SE(b)).
    Reference: statsmodels.discrete.discrete_model.NegativeBinomial (NB2).
    Non-identifiable, boundary, and failed fits explicitly fall back to exact Poisson.
    """
    _prob(alpha, "alpha")
    k, m = _units(events_by_unit, miles_by_unit)
    pooled = poisson_rate_ci(int(k.sum()), float(m.sum()), alpha)

    def fallback(reason: str) -> Rate:
        return Rate(pooled.rate, pooled.lower, pooled.upper, warning=reason)

    if len(k) < 3 or k.sum() == 0:
        return fallback("NB requires at least 3 positive-exposure units and nonzero events.")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            model = NegativeBinomial(k, np.ones((len(k), 1)), exposure=m, loglike_method="nb2")
            fit = model.fit(disp=False, maxiter=500)
        if not fit.mle_retvals.get("converged", False):
            return fallback("NB optimizer did not converge; exact Poisson shown.")
        beta, dispersion = fit.params
        se = float(fit.bse[0])
        if not np.isfinite([beta, dispersion, se]).all() or dispersion < 1e-7 or se <= 0:
            return fallback("NB dispersion not identifiable; exact Poisson shown.")
        z = norm.ppf(1 - alpha / 2)
        bounds = np.exp([beta - z * se, beta + z * se])
        if not np.isfinite(bounds).all():
            return fallback("NB interval is unstable; exact Poisson shown.")
        return Rate(
            float(np.exp(beta)),
            float(bounds[0]),
            float(bounds[1]),
            "Negative binomial · log-Wald",
            float(dispersion),
        )
    except (ValueError, np.linalg.LinAlgError, OverflowError, ZeroDivisionError):
        return fallback("NB fit failed; exact Poisson shown.")


def rate_ratio_ci(k1: int, m1: float, k2: int, m2: float, alpha: float = 0.05) -> dict:
    """Compare B/A rates with log-Wald CI and exact conditional binomial p-value.

    Args: A count/exposure and B count/exposure. Returns: ratio, bounds, p and method.
    Formula: RR=(k2/m2)/(k1/m1); SE(log RR)=sqrt(1/k1+1/k2).
    Under equal Poisson rates K_B | total ~ Binomial(total, m2/(m1+m2)).
    Reference: Przyborowski & Wilenski (1940). Zero counts use transformed exact
    Clopper-Pearson conditional bounds, with no arbitrary pseudo-count added.
    """
    _validate(k1, m1, alpha)
    _validate(k2, m2, alpha)
    total = k1 + k2
    if total == 0:
        return {
            "ratio": None,
            "lower": 0.0,
            "upper": None,
            "p": 1.0,
            "method": "Not identifiable: both groups have zero events",
        }
    test = binomtest(k2, total, m2 / (m1 + m2))
    if k1 == 0 or k2 == 0:
        ci = test.proportion_ci(confidence_level=1 - alpha, method="exact")
        return {
            "ratio": None if k1 == 0 else 0.0,
            "lower": ci.low / (1 - ci.low) * m1 / m2,
            "upper": None if ci.high == 1 else ci.high / (1 - ci.high) * m1 / m2,
            "p": float(test.pvalue),
            "method": "Exact conditional (zero-count case)",
        }
    ratio = (k2 / m2) / (k1 / m1)
    width = norm.ppf(1 - alpha / 2) * math.sqrt(1 / k1 + 1 / k2)
    return {
        "ratio": ratio,
        "lower": ratio * math.exp(-width),
        "upper": ratio * math.exp(width),
        "p": float(test.pvalue),
        "method": "Log-Wald CI; exact conditional Poisson p-value",
    }


def _plan_parameters(
    rate: float, reduction: float, alpha: float, power: float, dispersion: float, allocation: float
) -> None:
    _validate(0, rate, alpha)
    _prob(reduction, "relative reduction")
    _prob(power, "power")
    _prob(allocation, "allocation")
    if power <= 0.5:
        raise ValueError("target power must exceed 0.5")
    if not math.isfinite(dispersion) or dispersion < 1:
        raise ValueError("design effect must be finite and at least 1")


def miles_needed(
    baseline_rate: float,
    relative_reduction: float,
    alpha: float = 0.05,
    power: float = 0.80,
    dispersion: float = 1.0,
    allocation: float = 0.5,
    two_sided: bool = True,
) -> dict:
    """Normal-approximation two-rate planning with a constant quasi-Poisson design effect.

    Args: rate per mile, fractional reduction, alpha, power, design effect >=1,
        fraction of total miles in A, sidedness. Returns: miles and expected events.
    Formula: T=phi*(z_(1-alpha/2)+z_power)^2*(rA/f+rB/(1-f))/(rA-rB)^2.
    Reference: Wald normal approximation for independent Poisson rate differences.
    At rA=.001, reduction=.1, 80% power, 5% two-sided, f=.5 and phi=1,
    total T=2,982,574.299 miles; A=1,491,287.15 miles. This uses alternative
    variance in both critical terms and is an approximation, not an exact design.
    """
    _plan_parameters(baseline_rate, relative_reduction, alpha, power, dispersion, allocation)
    rb = baseline_rate * (1 - relative_reduction)
    z = norm.ppf(1 - alpha / (2 if two_sided else 1))
    variance = baseline_rate / allocation + rb / (1 - allocation)
    total = dispersion * (z + norm.ppf(power)) ** 2 * variance
    total /= (baseline_rate - rb) ** 2
    a, b = float(total * allocation), float(total * (1 - allocation))
    return {
        "miles_a": a,
        "miles_b": b,
        "total_miles": float(total),
        "events_a": a * baseline_rate,
        "events_b": b * rb,
        "design_effect": dispersion,
    }


def power_curve(
    baseline_rate: float,
    relative_reduction: float,
    miles_grid: Sequence[float],
    alpha: float = 0.05,
    dispersion: float = 1.0,
    allocation: float = 0.5,
    two_sided: bool = True,
) -> np.ndarray:
    """Normal-approximate power as a function of TOTAL miles across both arms.

    Args: planner parameters and finite nonnegative total miles. Returns: power array.
    Formula: Phi(delta*sqrt(T/(phi*V))-z)+Phi(-delta*sqrt(T/(phi*V))-z)
    for two-sided tests; only the first term for one-sided tests. Same V as miles_needed.
    Reference: normal Wald test under the alternative; independence and constant rates.
    """
    _plan_parameters(baseline_rate, relative_reduction, alpha, 0.8, dispersion, allocation)
    grid = np.asarray(miles_grid, dtype=float)
    if np.any(~np.isfinite(grid)) or np.any(grid < 0):
        raise ValueError("miles grid must be finite and nonnegative")
    rb = baseline_rate * (1 - relative_reduction)
    variance = dispersion * (baseline_rate / allocation + rb / (1 - allocation))
    shift = (baseline_rate - rb) * np.sqrt(grid / variance)
    z = norm.ppf(1 - alpha / (2 if two_sided else 1))
    return norm.cdf(shift - z) + (norm.cdf(-shift - z) if two_sided else 0)
