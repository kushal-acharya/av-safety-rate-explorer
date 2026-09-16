/** Browser estimators; numerically cross-checked against the Python/SciPy core. */
import jStat from 'jstat';
const probability = (x, name) => { if (!Number.isFinite(x) || x <= 0 || x >= 1) throw new Error(`${name} must be between 0 and 1`); };
function validate(k, m, alpha = .05) {
  probability(alpha, 'Alpha');
  if (!Number.isInteger(k) || k < 0 || !Number.isFinite(m) || m <= 0) throw new Error('Use nonnegative integer events and positive finite miles.');
}
export function poisson(k, m, alpha = .05) {
  validate(k, m, alpha);
  return { rate: k / m, lower: k ? jStat.gamma.inv(alpha / 2, k, 1) / m : 0,
    upper: jStat.gamma.inv(1 - alpha / 2, k + 1, 1) / m, method: 'Poisson exact', dispersion: 0 };
}
export function zeroBound(m, conf = .95) { validate(0, m); probability(conf, 'Confidence'); return -Math.log1p(-conf) / m; }
export function conditionalP(k1, m1, k2, m2) {
  validate(k1, m1); validate(k2, m2);
  const n = k1 + k2, p = m2 / (m1 + m2);
  if (!n) return 1;
  const logpmf = k => jStat.gammaln(n + 1) - jStat.gammaln(k + 1) - jStat.gammaln(n - k + 1) + k * Math.log(p) + (n - k) * Math.log1p(-p);
  const observed = logpmf(k2); let sum = 0;
  for (let k = 0; k <= n; k++) { const lp = logpmf(k); if (lp <= observed + 1e-7) sum += Math.exp(lp); }
  return Math.min(1, sum);
}
export function ratio(k1, m1, k2, m2, alpha = .05) {
  validate(k1, m1, alpha); validate(k2, m2, alpha);
  const n = k1 + k2, p = conditionalP(k1, m1, k2, m2);
  if (!n) return { ratio: null, lower: 0, upper: null, p, method: 'Not identifiable: both groups have zero events' };
  if (!k1 || !k2) {
    const lo = k2 ? jStat.beta.inv(alpha / 2, k2, n - k2 + 1) : 0;
    const hi = k2 === n ? 1 : jStat.beta.inv(1 - alpha / 2, k2 + 1, n - k2);
    return { ratio: k1 ? 0 : null, lower: lo / (1 - lo) * m1 / m2,
      upper: hi === 1 ? null : hi / (1 - hi) * m1 / m2, p, method: 'Exact conditional (zero-count case)' };
  }
  const rr = (k2 / m2) / (k1 / m1), w = jStat.normal.inv(1 - alpha / 2, 0, 1) * Math.sqrt(1 / k1 + 1 / k2);
  return { ratio: rr, lower: rr * Math.exp(-w), upper: rr * Math.exp(w), p, method: 'Log-Wald CI · exact conditional Poisson test' };
}
function plannerParams(rate, reduction, alpha, power, phi, allocation) {
  validate(0, rate, alpha); probability(reduction, 'Reduction'); probability(power, 'Power'); probability(allocation, 'Allocation');
  if (power <= .5 || !Number.isFinite(phi) || phi < 1) throw new Error('Power must exceed 50%; design effect must be at least 1.');
}
export function plan(rate, reduction, alpha = .05, power = .8, phi = 1, allocation = .5, twoSided = true) {
  plannerParams(rate, reduction, alpha, power, phi, allocation);
  const rb = rate * (1 - reduction), z = jStat.normal.inv(1 - alpha / (twoSided ? 2 : 1), 0, 1);
  const total = phi * (z + jStat.normal.inv(power, 0, 1)) ** 2 * (rate / allocation + rb / (1 - allocation)) / (rate - rb) ** 2;
  return { total_miles: total, design_effect: phi, miles_a: total * allocation, miles_b: total * (1 - allocation), events_a: total * allocation * rate, events_b: total * (1 - allocation) * rb };
}
export function powerAt(total, rate, reduction, alpha = .05, phi = 1, allocation = .5, twoSided = true) {
  plannerParams(rate, reduction, alpha, .8, phi, allocation);
  if (!Number.isFinite(total) || total < 0) throw new Error('Total miles must be finite and nonnegative.');
  const rb = rate * (1 - reduction), shift = (rate - rb) * Math.sqrt(total / (phi * (rate / allocation + rb / (1 - allocation))));
  const z = jStat.normal.inv(1 - alpha / (twoSided ? 2 : 1), 0, 1);
  return jStat.normal.cdf(shift - z, 0, 1) + (twoSided ? jStat.normal.cdf(-shift - z, 0, 1) : 0);
}
export function interval(row, fit, method, alpha) {
  const exact = poisson(row.events, row.miles, alpha);
  const wantNB = method === 'nb' || (method === 'auto' && fit?.overdispersed);
  if (row.events && wantNB && fit?.method?.startsWith('Negative') && Number.isFinite(fit.log_se)) {
    const width = jStat.normal.inv(1 - alpha / 2, 0, 1) * fit.log_se;
    return { rate: fit.rate, lower: Math.exp(Math.log(fit.rate) - width), upper: Math.exp(Math.log(fit.rate) + width), method: 'NB · log-Wald', phi: fit.phi, warning: '' };
  }
  return { ...exact, phi: fit?.phi ?? 1, warning: wantNB ? fit?.warning || 'NB unavailable for this group; exact Poisson shown.' : '' };
}
