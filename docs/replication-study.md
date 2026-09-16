# Reproduction note 001: a published Waymo crash-rate comparison

[Open the study](https://vivaran.news/waymo-project/?tab=replication&study=sf-injury&tails=paper_code)

## Question and scope

Can the city-level results in Table 7 of *Comparison of Waymo Rider-Only Crash Data
to Human Benchmarks at 7.1 Million Miles* be recovered from the publication's inputs?

The primary comparison is **San Francisco, any-injury-reported crashes, against the
Blincoe-adjusted human benchmark**. Three companion comparisons reproduce the other
Appendix A.3 reference cases: Phoenix injury, San Francisco police-reported, and
Phoenix police-reported. These were selected because the authors supply explicit
reference inputs and outputs, not because of the direction of their results.

This is a computational reproduction from author-supplied classifications and
benchmark estimates. It does not independently reconstruct the state human-crash
databases, verify injury adjudication, or audit the completeness of SGO reporting.
It does not reproduce every result in the paper or estimate a pooled fleet effect.

## Frozen source and population

- Kusano et al., accepted manuscript, **arXiv:2312.12675v3**, October 24, 2024.
- [Versioned PDF](https://arxiv.org/pdf/2312.12675v3).
- [Journal DOI](https://doi.org/10.1080/15389588.2024.2380786).
- Waymo rider-only operations through **October 31, 2023**; human benchmarks use the
  paper's 2022 passenger-vehicle, surface-street data. These periods are deliberately
  distinguished, not described as contemporaneous randomized controls.
- The exact PDF SHA-256 and processed-input hashes are in
  [the manifest](../data/processed/replication/manifest.json).

The current safety-impact dashboard and the later 56.7-million-mile paper cover
different periods and definitions. Their data are **not** inputs to this study.
California DMV disengagement counts and test mileage are also **not** used.

## Inputs and extraction

| File | Source | Treatment |
|---|---|---|
| `events.csv` | Appendix A.1, PDF pages 19–20 | All 73 event/membership rows extracted; flags preserved |
| `comparisons.csv` | Table 2 (p. 6), Table 7 (p. 10), Appendix A.3 Listing 2 (p. 22) | Four documented numeric transcriptions at published precision |
| `manifest.json` | Source/provenance record | Frozen hashes, extraction notes and limitations |

There are 38 Phoenix, 34 San Francisco and one Los Angeles listed events. The
in-transport/impacted subset contains 63 records, of which four satisfy any injury
and 15 satisfy police reported. Two pre-SGO cases remain in the list with identifiers
`victor-2023-1` and `victor-2023-4`; neither is an injury case. They are not fabricated
SGO IDs. The publication had already resolved duplicate reports: no additional
deduplication or reclassification is applied.

The primary path is 34 listed San Francisco events → 29 in-transport/impacted →
one injury event, `30270-6336`. All excluded records remain downloadable with their
membership flags. Los Angeles remains in the source audit, but is outside the four
reference comparisons; its exposure is not silently pooled with the selected city.

Benchmark/reference rows are transcribed rather than automatically parsed. The
source-verification command re-extracts the 73 event rows and compares them with the
committed input; hashes also protect the four transcribed rows from unnoticed changes.
A hash proves file identity, not the factual accuracy of the source or transcription.

## Calculation

For the primary comparison:

- ADS count **Y = 1**, independently summed from the event memberships.
- ADS exposure **t = 1,755,000 rider-only miles**, from Appendix A.3.
- Human benchmark **r = 5.82 crashed vehicles per million miles**.
- Human exposure **s = 862,000,000 miles**, from the same published reference case.
- Reconstructed benchmark count **X = r × s / 1,000,000 = 5,016.84**.

The fractional X is the authors' adjusted/rounded benchmark input, not an observed
integer crash count. The Blincoe injury underreporting adjustment is already embedded
in r; it is not applied a second time.

The ADS rate is `Y/t × 1e6 = 0.56980057` per million miles. The rate ratio is
`(Y/t)/(X/s) = 0.09790388`, or a **90.2096% lower observed rate**. At the benchmark
rate, the same Waymo exposure corresponds to **10.2141 expected events**. That is
not a count observed in a randomized control arm.

The ADS rate's two-sided 95% Garwood interval is approximately **[0.014426,
3.174726] per million miles**. The ratio intervals use beta-prime quantiles:

```text
lower = (s/t) × beta_prime_quantile(q, Y, X+1)
upper = (s/t) × beta_prime_quantile(1-q, Y+1, X)
```

The point estimate and bounds are calculated from the event counts and benchmark
inputs. Published ratio/interval values are read only as separate audit targets.

## Interval convention finding

Equation 2 uses `q = alpha/2`, giving **0.025 and 0.975** at alpha 0.05.
Appendix A.3 Listing 1 first halves alpha for positive counts and then uses alpha/2
in the quantile calls, giving **0.0125 and 0.9875**. All four reference cases have
positive counts.

We implement both paths explicitly. The paper-code path reproduces the reference
outputs, including the wider San Francisco injury interval of approximately
**[0.001231, 0.625053]**, against the published **[0.001, 0.62]**.
The equation path yields a conventional 95% central-probability interval in the model.
The code path has 97.5% central probability for these positive-count cases, despite
the source's 95% label. This is an observable difference between the displayed
equation and example code; it is not a claim about the authors' intent.

In the Phoenix injury case, the paper-code upper limit is above 1 while the
Equation 2 upper limit is below 1. The interface exposes that sensitivity rather
than selecting a convention to obtain a preferred conclusion.

These nominal model probabilities are not guarantees of frequentist coverage for
adjusted benchmark estimates. Uncertainty in the underreporting correction and other
systematic biases is not captured by this calculation. No simulation-based coverage
validation is claimed.

## Agreement and discrepancies

All four extracted event counts match exactly. All 12 rate-ratio and endpoint
checks have absolute difference **less than 0.01**, the tolerance used in the
paper's own Appendix A.3 Listing 2. Thus **16/16 reference checks pass**.

This is agreement within the published example's tolerance, not bit-for-bit
agreement or necessarily identical nearest-decimal rounding. For example, the
primary upper endpoint is 0.625053 versus the printed 0.62, a difference of
0.005053. The UI and [results CSV](../data/processed/replication/results.csv) show
each difference. Rounded inputs and implementation precision limit exact recovery;
we do not assign a specific cause to each remaining difference.

## Reproduce and verify

From a checkout of the repository:

```bash
# Offline: rebuild the study and browser artifacts from committed inputs.
uv run python scripts/reproduce_study.py

# Fetch the frozen PDF, verify its hash, re-extract event rows, then rebuild.
uv run --group research python scripts/reproduce_study.py --from-source

# CI: verify generated artifacts are current without editing files or networking.
uv run python scripts/reproduce_study.py --check
uv run pytest tests/test_replication.py -q
```

The optional `research` dependency group installs the PDF parser. It is not needed
by the deployed website or offline calculation. Original PDFs remain gitignored.
The browser renders the Python-generated artifact, avoiding a second implementation
of these sensitive calculations in JavaScript.

Tests include the published reference values; an independent beta/binomial identity;
the zero-event closed-form upper bound; invalid inputs; hash drift; cohort accounting;
and equality between freshly computed results and the browser's committed artifact.

## Interpretation limits

This historical, observational comparison is specific to the cited geography,
outcome, exposure and benchmark. It does not show a causal effect, contemporary
fleet performance, software-release improvement, deployment readiness, or a complete
safety case. Author-supplied classification and benchmark construction remain
dependencies. No spatial reweighting, adjustment for multiple comparisons, or
propagation of underreporting uncertainty is performed in this reproduction.

The useful contribution is a traceable recovery of selected published calculations,
with the interval-convention difference made inspectable and the boundaries stated.
