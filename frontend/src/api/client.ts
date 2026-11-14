import type {
  GeoPoint,
  VariableInfo,
  TrendAnalysisResponse,
  CompareResponse,
  VerifiedDatasetResponse,
} from '../types';

const API_BASE = '/api/v1';

export async function fetchHealth(): Promise<{ status: string; version: string }> {
  const res = await fetch(`${API_BASE}/health`);
  if (!res.ok) throw new Error('Backend health check failed');
  return res.json();
}

export async function fetchVariables(): Promise<VariableInfo[]> {
  const res = await fetch(`${API_BASE}/variables?include_planned=true`);
  if (!res.ok) throw new Error('Failed to load variables');
  const data = await res.json();
  return data.items || [];
}

export async function searchLocations(query: string): Promise<GeoPoint[]> {
  if (!query || query.trim().length === 0) return [];
  const res = await fetch(`${API_BASE}/locations/search?q=${encodeURIComponent(query)}&limit=8`);
  if (!res.ok) return [];
  const data = await res.json();
  return (data.items || []).map((item: any) => ({
    latitude: item.latitude,
    longitude: item.longitude,
    name: item.display_name || item.name,
    country: item.country,
    region: item.region,
  }));
}

export async function fetchVerifiedDataset(): Promise<VerifiedDatasetResponse> {
  const res = await fetch(`${API_BASE}/datasets/verified`);
  if (!res.ok) throw new Error('Failed to load verified dataset stations');
  return res.json();
}

export async function runTrendAnalysis(params: {
  variable: string;
  location: GeoPoint;
  start_date: string;
  end_date: string;
  frequency?: string;
  methods?: string[];
  seasonal_adjustment?: boolean;
  alpha?: number;
}): Promise<TrendAnalysisResponse> {
  const res = await fetch(`${API_BASE}/analysis/trend`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      variable: params.variable,
      source: 'NASA_POWER',
      location: params.location,
      start_date: params.start_date,
      end_date: params.end_date,
      frequency: params.frequency || 'monthly',
      methods: params.methods || ['ols', 'mann_kendall', 'theil_sen'],
      seasonal_adjustment: params.seasonal_adjustment ?? true,
      alpha: params.alpha ?? 0.05,
    }),
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    const message = errorData.error?.message || errorData.detail || 'Analysis request failed';
    throw new Error(message);
  }

  return res.json();
}

export async function runCompareAnalysis(params: {
  variable: string;
  location_a: GeoPoint;
  location_b: GeoPoint;
  start_date: string;
  end_date: string;
  seasonal_adjustment?: boolean;
}): Promise<CompareResponse> {
  const res = await fetch(`${API_BASE}/analysis/compare`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      variable: params.variable,
      source: 'NASA_POWER',
      location_a: params.location_a,
      location_b: params.location_b,
      start_date: params.start_date,
      end_date: params.end_date,
      frequency: 'monthly',
      seasonal_adjustment: params.seasonal_adjustment ?? true,
    }),
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    const message = errorData.error?.message || errorData.detail || 'Comparison request failed';
    throw new Error(message);
  }

  return res.json();
}

export function getExportUrl(analysisId: string, format: 'csv' | 'json' | 'pdf'): string {
  return `${API_BASE}/export/${analysisId}?format=${format}`;
}
