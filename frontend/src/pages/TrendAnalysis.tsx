import React from 'react';
import {
  TrendingUp,
  Download,
  ShieldCheck,
  AlertTriangle,
  FileText,
  FileSpreadsheet,
  Code,
  Calendar,
  Layers,
  MapPin,
  RefreshCw,
  BarChart2,
} from 'lucide-react';
import { TimeSeriesChart } from '../components/TimeSeriesChart';
import { StatCard } from '../components/StatCard';
import { getExportUrl } from '../api/client';
import type { TrendAnalysisResponse } from '../types';

interface TrendAnalysisProps {
  data: TrendAnalysisResponse | null;
  onRefresh: () => void;
  onNavigateToExplorer: () => void;
}

export const TrendAnalysis: React.FC<TrendAnalysisProps> = ({
  data,
  onRefresh,
  onNavigateToExplorer,
}) => {
  if (!data) {
    return (
      <div className="py-20 text-center space-y-4 glass-panel max-w-xl mx-auto rounded-3xl p-10 border border-slate-800">
        <div className="w-16 h-16 mx-auto rounded-2xl bg-emerald-500/10 flex items-center justify-center text-emerald-400">
          <TrendingUp className="w-8 h-8" />
        </div>
        <h2 className="text-2xl font-bold text-white">No Active Trend Analysis</h2>
        <p className="text-sm text-slate-400">
          Choose a location and variable in Earth Explorer to compute empirical trend statistics.
        </p>
        <button
          onClick={onNavigateToExplorer}
          className="px-6 py-3 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-navy-950 font-bold text-sm shadow-lg shadow-emerald-500/20"
        >
          Go to Earth Explorer
        </button>
      </div>
    );
  }

  const { ols, mann_kendall, theil_sen, quality, interpretation, provenance, request } = data;
  const units = provenance.units || 'units';

  const isSig = ols?.significant ?? false;
  const slopeYear = ols?.slope_per_year ?? 0;
  const slopeDecade = ols?.slope_per_decade ?? 0;
  const pVal = ols?.p_value ?? 1;

  const modeBadgeText =
    provenance.retrieval_mode === 'dataset'
      ? 'Climato 2000-2025 Dataset'
      : provenance.retrieval_mode === 'live'
      ? 'Live NASA POWER API'
      : 'Demonstration Snapshot';

  return (
    <div className="space-y-8 py-4">
      {/* Top Banner & Metadata */}
      <div className="glass-panel p-6 rounded-3xl border border-slate-800 space-y-4">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="px-2.5 py-0.5 rounded-full text-xs font-bold uppercase bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">
                {provenance.variable}
              </span>
              <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-slate-800 text-slate-300 border border-slate-700">
                {modeBadgeText}
              </span>
              <span className="text-xs text-slate-400">Analysis ID: {data.analysis_id.slice(0, 8)}</span>
            </div>
            <h1 className="text-3xl font-extrabold text-white tracking-tight">
              {provenance.variable_name} Trend Analysis
            </h1>
            <p className="text-sm text-slate-300 flex items-center gap-2">
              <MapPin className="w-4 h-4 text-emerald-400" />
              <strong>{request.location.name || 'Selected Location'}</strong> ({request.location.latitude.toFixed(4)}°N, {request.location.longitude.toFixed(4)}°E)
            </p>
          </div>

          {/* Action & Export buttons */}
          <div className="flex flex-wrap items-center gap-2 self-start md:self-auto">
            <button
              onClick={onRefresh}
              className="p-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition-colors"
              title="Re-run analysis"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
            <a
              href={getExportUrl(data.analysis_id, 'csv')}
              download
              className="px-3.5 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold border border-slate-700 flex items-center gap-1.5 transition-colors"
            >
              <FileSpreadsheet className="w-3.5 h-3.5 text-emerald-400" />
              CSV
            </a>
            <a
              href={getExportUrl(data.analysis_id, 'json')}
              download
              className="px-3.5 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold border border-slate-700 flex items-center gap-1.5 transition-colors"
            >
              <Code className="w-3.5 h-3.5 text-sky-400" />
              JSON
            </a>
            <a
              href={getExportUrl(data.analysis_id, 'pdf')}
              download
              className="px-3.5 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold shadow-md shadow-emerald-500/20 flex items-center gap-1.5 transition-colors"
            >
              <FileText className="w-3.5 h-3.5" />
              Report (PDF)
            </a>
          </div>
        </div>
      </div>

      {/* Primary Key Statistics Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          label="OLS Rate of Change"
          value={`${slopeYear > 0 ? '+' : ''}${slopeYear.toFixed(4)}`}
          unit={`${units}/yr`}
          subValue={`${slopeDecade > 0 ? '+' : ''}${slopeDecade.toFixed(3)} ${units}/decade`}
          badge={{
            text: ols?.direction ? ols.direction.replace(/_/g, ' ') : 'trend',
            variant: isSig ? 'success' : 'neutral',
          }}
          tooltip="Ordinary Least Squares slope per year."
        />

        <StatCard
          label="Statistical Significance"
          value={pVal < 0.0001 ? '< 0.0001' : pVal.toFixed(4)}
          unit="p-value"
          subValue={`Threshold: α = ${request.alpha}`}
          badge={{
            text: isSig ? 'Significant' : 'Not Significant',
            variant: isSig ? 'success' : 'warning',
          }}
          tooltip="Two-sided hypothesis test (p < 0.05 indicates statistical significance)."
        />

        <StatCard
          label="Mann-Kendall Test"
          value={mann_kendall?.tau ? mann_kendall.tau.toFixed(3) : 'n/a'}
          unit="Kendall τ"
          subValue={`Z = ${mann_kendall?.z_statistic.toFixed(2) ?? 'n/a'}`}
          badge={{
            text: mann_kendall?.trend ? mann_kendall.trend.replace(/_/g, ' ') : 'monotonic',
            variant: mann_kendall?.significant ? 'success' : 'neutral',
          }}
          tooltip="Non-parametric rank correlation test for monotonic trends."
        />

        <StatCard
          label="Theil-Sen Robust Slope"
          value={`${theil_sen?.slope_per_year ? (theil_sen.slope_per_year > 0 ? '+' : '') + theil_sen.slope_per_year.toFixed(4) : 'n/a'}`}
          unit={`${units}/yr`}
          subValue={`R² = ${ols?.r_squared.toFixed(3) ?? '0.000'}`}
          badge={{
            text: 'Median Slope',
            variant: 'info',
          }}
          tooltip="Robust median-of-pairwise-slopes estimator resistant to outliers."
        />
      </div>

      {/* Scientific Interpretation Card */}
      <div className="glass-panel p-6 rounded-3xl border border-emerald-500/30 bg-gradient-to-r from-emerald-950/30 via-slate-900/60 to-navy-950 space-y-4">
        <div className="flex items-center gap-2">
          <ShieldCheck className="w-5 h-5 text-emerald-400" />
          <h3 className="text-lg font-bold text-white tracking-tight">
            {interpretation.headline}
          </h3>
        </div>
        <p className="text-sm text-slate-200 leading-relaxed font-normal">
          {interpretation.narrative}
        </p>
        <p className="text-xs text-slate-400 border-t border-slate-800/80 pt-3">
          <strong>Statistical Conclusion:</strong> {interpretation.significance_statement}
        </p>
      </div>

      {/* Main Historical Time-Series Chart */}
      <div className="glass-panel p-6 rounded-3xl space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div>
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <BarChart2 className="w-5 h-5 text-emerald-400" />
              Historical Observations & Fitted Trend Line
            </h2>
            <p className="text-xs text-slate-400">
              Monthly values from {quality.period_start} to {quality.period_end} with 95% Confidence Band
            </p>
          </div>
          <div className="text-xs font-mono text-slate-400">
            {quality.n_valid} observations ({quality.period_years.toFixed(1)} years)
          </div>
        </div>

        <TimeSeriesChart data={data} showConfidenceInterval={true} />
      </div>

      {/* Data Quality & Diagnostics Table */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="glass-panel p-6 rounded-3xl space-y-4">
          <h3 className="text-base font-bold text-white flex items-center gap-2">
            <Layers className="w-4 h-4 text-emerald-400" />
            Empirical Data Quality Checks
          </h3>
          <div className="space-y-2">
            {quality.checks.map((c, i) => (
              <div
                key={i}
                className="flex items-center justify-between p-3 rounded-xl bg-slate-900/60 border border-slate-800 text-xs"
              >
                <span className="text-slate-300 font-medium capitalize">
                  {c.name.replace(/_/g, ' ')}
                </span>
                <span
                  className={`px-2 py-0.5 rounded text-[11px] font-bold uppercase ${
                    c.status === 'pass'
                      ? 'bg-emerald-500/20 text-emerald-400'
                      : 'bg-amber-500/20 text-amber-400'
                  }`}
                >
                  {c.status}
                </span>
              </div>
            ))}
          </div>
        </div>

        <div className="glass-panel p-6 rounded-3xl space-y-4">
          <h3 className="text-base font-bold text-white flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            Provenance & Metadata
          </h3>
          <div className="text-xs space-y-2 text-slate-300">
            <div className="flex justify-between py-1.5 border-b border-slate-800">
              <span className="text-slate-400">Data Source:</span>
              <span className="font-semibold text-white">{provenance.provider}</span>
            </div>
            <div className="flex justify-between py-1.5 border-b border-slate-800">
              <span className="text-slate-400">Underlying Model:</span>
              <span className="font-semibold text-white">MERRA-2 Reanalysis</span>
            </div>
            <div className="flex justify-between py-1.5 border-b border-slate-800">
              <span className="text-slate-400">Spatial Resolution:</span>
              <span className="font-mono text-slate-200">{provenance.spatial_resolution}</span>
            </div>
            <div className="flex justify-between py-1.5 border-b border-slate-800">
              <span className="text-slate-400">Analysis Engine:</span>
              <span className="font-mono text-emerald-400">EarthTrend v{provenance.engine_version}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
