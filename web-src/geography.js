/**
 * Fixed-benchmark sensitivity, validated against the Python reference grid.
 * @param {import('./geography-types').ScenarioInputs} row
 * @param {number} [mix] Fraction toward Waymo mileage shares, in [0, 1].
 * @param {number} [stress] Positive multiplier on the human benchmark.
 * @returns {import('./geography-types').SpatialScenario}
 */
export function spatialScenario(row, mix = 1, stress = 1) {
  if (!Number.isFinite(mix) || mix < 0 || mix > 1)
    throw new Error("Mix must be in [0, 1].");
  if (!Number.isFinite(stress) || stress <= 0)
    throw new Error("Stress must be positive and finite.");
  const benchmark = row.baseline_ipmm * (1 + mix * (row.factor - 1)) * stress;
  if (!Number.isFinite(benchmark) || benchmark <= 0)
    throw new Error("Invalid benchmark.");
  const ratio = row.waymo_ipmm / benchmark;
  return {
    benchmark_ipmm: benchmark,
    ratio,
    ratio_lower: row.waymo_lower / benchmark,
    ratio_upper: row.waymo_upper / benchmark,
    reduction_percent: (1 - ratio) * 100,
    reduction_lower: (1 - row.waymo_upper / benchmark) * 100,
    reduction_upper: (1 - row.waymo_lower / benchmark) * 100,
    expected_events: (benchmark * row.waymo_miles) / 1e6,
  };
}
