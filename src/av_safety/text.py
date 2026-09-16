"""Methods text shared by the Streamlit interface."""

METHODS = r"""
### What these data can say
This is an independent project using **California DMV disengagement reports**, not crash data.
An intervention may be precautionary. Reporting practices, routes, weather and test difficulty
vary; **these are not company safety rankings**. The historical snapshot covers 2020–2024,
retrieved September 16, 2026 UTC. Each reporting year runs December–November.
Safety-driver and driverless permit reports remain separate. Commercial deployment,
private-road testing and out-of-state mileage are not the exposure denominator here.

### Rate estimation
Observed rate = events / miles. Garwood's two-sided exact interval is
$[\chi^2_{\alpha/2,2k},\chi^2_{1-\alpha/2,2k+2}]/(2m)$, with lower bound 0 at k=0.
For zero events, the **two-sided 95% upper bound is 3.689/miles**. The separate
**one-sided 95% rule of three is 2.996/miles**. Neither implies zero underlying risk.

Auto checks VIN-year Pearson dispersion: $\phi=\sum(k_i-\mu_i)^2/\mu_i/(n-1)$.
When phi > 1 and its asymptotic p < .05, at least three positive-exposure units and an
identifiable converged fit allow NB2: $E[K_i]=m_i e^\beta$;
$Var(K_i)=\mu_i+\alpha_{NB}\mu_i^2$. Dispersion is fitted by maximum likelihood.
The NB interval is log-Wald, not exact. Failed fits explicitly fall back to Poisson.
NB fitted rates may differ from observed pooled rates. Its interval need not contain
the Poisson interval. Sparse counts weaken the dispersion diagnostic; VINs repeated
across years may remain correlated.

### Comparisons
B/A uses a log-Wald interval for positive counts with SE = sqrt(1/kA + 1/kB), and an
exact conditional binomial test under equal Poisson rates. Zero-count groups use exact
conditional Clopper–Pearson bounds, without pseudo-counts. Two zero-count groups do not
identify a ratio. All group rates in Compare use exact Poisson intervals. Overdispersion
may make comparison inference too optimistic. No multiple-comparison adjustment is made.
A company-year is **not a randomized release**; observational differences are not causal.

### Experiment planner
The normal approximation assumes independent arms, constant rates, fixed analysis and
known design effect phi: $T=\phi(z_{crit}+z_{power})^2[r_A/f+r_B/(1-f)]/(r_A-r_B)^2$.
T is **total miles**. Expected events are the rate times arm-specific exposure.
Phi is a constant quasi-Poisson variance multiplier, **not NB2 alpha**. An empirical
VIN-year phi is only a sensitivity assumption, not a validated release-level effect.
Clustering, sequential monitoring and shifting operating domains need richer models.
At 1 event per 1,000 miles, a 10% reduction, 80% power, two-sided 5% alpha, phi=1,
and equal allocation, total exposure is about **2,982,574 miles**.

### Source audit
All 128 annual manufacturer/year/mode event counts reconcile with 22,958 detailed events.
47 missing annual mileage cells were reconstructed from monthly reports. 13 date anomalies
are flagged and retained under the reported year. One zero-mile VIN with an event disables
NB fitting for the affected group. See `data/README.md` and the source manifest for hashes.
Event context groups initiator, location and cause while retaining Unknown and zero-event
categories. Each category uses the full selected exposure; roadway-specific mileage is
unavailable. Category intervals always use exact Poisson. Ambiguous source labels stay
Unknown, and original labels remain in the detailed event table. Cause categories are
simple first-match keyword buckets, not validated causal labels.

References: Garwood (1936), Biometrika 28:437–442; McCullagh & Nelder (1989);
SciPy chi-square/binomial inference; statsmodels NegativeBinomial (NB2).
"""
