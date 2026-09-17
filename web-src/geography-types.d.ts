/** Rates are events per million miles; exposure is miles, not millions of miles. */
export interface ScenarioInputs {
  baseline_ipmm: number;
  factor: number;
  waymo_ipmm: number;
  waymo_lower: number;
  waymo_upper: number;
  waymo_miles: number;
}
export interface SpatialScenario {
  benchmark_ipmm: number;
  ratio: number;
  ratio_lower: number;
  ratio_upper: number;
  reduction_percent: number;
  reduction_lower: number;
  reduction_upper: number;
  expected_events: number;
}
export interface GeographyComparison extends ScenarioInputs {
  city: string;
  metric: string;
  label: string;
  metric_label: string;
  events: number;
  published_events: number;
  published_matched_ipmm: number;
  matched_ipmm: number;
  cells: number;
  cell_miles: number;
  coverage: number;
  unallocated_miles: number;
  benchmark_delta: number;
  benchmark_matches: boolean;
  count_matches: boolean;
  event_rows: number[];
  bands: Array<{
    band: number;
    cells: number;
    human_share: number;
    waymo_share: number;
    relative_rate_min: number;
    relative_rate_max: number;
  }>;
  unadjusted: SpatialScenario;
  matched: SpatialScenario;
  scenarios: Array<SpatialScenario & { mix: number; stress: number }>;
}
export interface GeographySnapshot {
  study_id: string;
  release_date: string;
  period: string;
  benchmark_year: number;
  source_manifest: Record<string, unknown>;
  comparisons: GeographyComparison[];
  audit: {
    unique_cells: number;
    cell_outcome_rows: number;
    source_event_rows: number;
    benchmark_checks: number;
    count_checks: number;
  };
}
