export interface GeoPoint {
  latitude: number;
  longitude: number;
  name?: string;
  country?: string;
  region?: string;
}

export interface VariableInfo {
  id: string;
  code: string;
  scientific_name: string;
  display_name: string;
  description: string;
  units: string;
  category: string;
  provider: string;
  dataset: string;
  product_type: string;
  temporal_coverage: string;
  spatial_coverage: string;
  spatial_resolution: string;
  frequencies: string[];
  source_documentation: string;
  limitations: string[];
  status: string;
  supported_by: string;
  color: string;
}

export interface TrendLinePoint {
  date: string;
  observed?: number;
  fitted: number;
  lower?: number;
  upper?: number;
}

export interface LinearTrendResult {
  slope_per_year: number;
  slope_per_decade: number;
  intercept: number;
  standard_error: number;
  p_value: number;
  r_squared: number;
  adjusted_r_squared: number;
  confidence_interval_95: [number, number];
  confidence_interval_95_per_decade: [number, number];
  t_statistic: number;
  degrees_of_freedom: number;
  direction: 'increasing' | 'decreasing' | 'no_detectable_trend';
  significant: boolean;
  unit_rate_label: string;
  unit_decade_label: string;
}

export interface MannKendallResult {
  trend: 'increasing' | 'decreasing' | 'no_detectable_trend';
  significant: boolean;
  p_value: number;
  z_statistic: number;
  tau: number;
  score_s: number;
  var_s: number;
}

export interface TheilSenResult {
  slope_per_year: number;
  slope_per_decade: number;
  intercept: number;
  confidence_interval_95: [number, number];
  direction: 'increasing' | 'decreasing' | 'no_detectable_trend';
}

export interface MonthlyClimatology {
  month: number;
  mean: number;
  std: number;
  count: number;
}

export interface SeasonalResult {
  applied: boolean;
  baseline_start?: string;
  baseline_end?: string;
  climatology: MonthlyClimatology[];
  note: string;
}

export interface DataQuality {
  n_valid: number;
  n_expected: number;
  n_missing: number;
  missing_pct: number;
  period_start?: string;
  period_end?: string;
  period_years: number;
  is_constant: boolean;
  lag1_autocorrelation?: number;
  autocorrelation_warning: boolean;
  irregular_sampling: boolean;
  min_observations_required: int;
  sufficient: boolean;
  checks: { name: string; status: 'pass' | 'warning' | 'fail'; message: string }[];
  warnings: string[];
}

export interface DistributionBin {
  label: string;
  count: number;
}

export interface Interpretation {
  headline: string;
  narrative: string;
  significance_statement: string;
  practical_note: string;
  limitations: string[];
}

export interface DataProvenance {
  variable: string;
  variable_name: string;
  units: string;
  provider: string;
  dataset: string;
  product_type: string;
  spatial_resolution: string;
  source_url: string;
  requested_start: string;
  requested_end: string;
  analyzed_start?: string;
  analyzed_end?: string;
  frequency: string;
  retrieval_mode: 'live' | 'cache' | 'demo' | 'mixed' | 'dataset';
  retrieved_at: string;
  engine_version: string;
}

export interface TrendAnalysisResponse {
  analysis_id: string;
  kind: 'trend';
  request: {
    variable: string;
    source: string;
    location: GeoPoint;
    start_date: string;
    end_date: string;
    frequency: string;
    methods: string[];
    seasonal_adjustment: boolean;
    alpha: number;
  };
  provenance: DataProvenance;
  quality: DataQuality;
  observations: { date: string; value: number; anomaly?: number }[];
  trend_line: TrendLinePoint[];
  ols?: LinearTrendResult;
  mann_kendall?: MannKendallResult;
  theil_sen?: TheilSenResult;
  seasonal?: SeasonalResult;
  distribution: DistributionBin[];
  interpretation: Interpretation;
  warnings: { code: string; message: string; severity: 'info' | 'warning' | 'critical' }[];
  created_at: string;
  cached: boolean;
}

export interface ComparisonSummary {
  descriptive_only: boolean;
  slope_difference_per_year?: number;
  slope_difference_per_decade?: number;
  direction_a?: string;
  direction_b?: string;
  aligned_observations: number;
  normalized: boolean;
  summary: string;
  note: string;
}

export interface CompareResponse {
  comparison_id: string;
  kind: 'compare';
  location_a: TrendAnalysisResponse;
  location_b: TrendAnalysisResponse;
  comparison: ComparisonSummary;
  created_at: string;
}

export interface GridStation {
  point_id: string;
  name: string;
  latitude: number;
  longitude: number;
}

export interface VerifiedDatasetResponse {
  available: boolean;
  dataset_name: string;
  source: string;
  coverage: {
    period: string;
    region: string;
    latitudes: number[];
    longitudes: number[];
  };
  variables: { code: string; name: string; units: string }[];
  total_observations: number;
  stations_count: number;
  stations: GridStation[];
}
