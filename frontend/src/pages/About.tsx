import React from 'react';
import { ShieldCheck, BookOpen, ExternalLink, Globe2, Layers, Cpu, Award } from 'lucide-react';

export const About: React.FC = () => {
  return (
    <div className="space-y-12 py-6 max-w-4xl mx-auto">
      {/* Header */}
      <div className="text-center space-y-3">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/25 text-xs font-bold uppercase tracking-wider">
          NASA Space Apps Challenge 2026
        </div>
        <h1 className="text-4xl font-extrabold text-white tracking-tight">
          About EarthTrend
        </h1>
        <p className="text-slate-300 text-base leading-relaxed">
          Open-science environmental trend intelligence built to provide transparent, verified Earth data analytics without black-box abstractions.
        </p>
      </div>

      {/* Core NASA Challenge Pillars */}
      <div className="glass-panel p-8 rounded-3xl space-y-6 border border-slate-800">
        <h2 className="text-xl font-bold text-white flex items-center gap-2">
          <Award className="w-5 h-5 text-emerald-400" />
          The NASA Challenge Objective
        </h2>
        <p className="text-sm text-slate-300 leading-relaxed">
          EarthTrend solves the challenge of turning multi-decadal Earth observation data into actionable, statistically sound insights. By combining reanalysis datasets, empirical testing, and interactive geospatial mapping, EarthTrend empowers scientists, educators, and the public to examine climate trends with complete mathematical transparency.
        </p>
      </div>

      {/* Scientific Methodology */}
      <div className="glass-panel p-8 rounded-3xl space-y-6 border border-slate-800">
        <h2 className="text-xl font-bold text-white flex items-center gap-2">
          <BookOpen className="w-5 h-5 text-emerald-400" />
          Rigorous Statistical Methodology
        </h2>

        <div className="space-y-4 text-sm text-slate-300">
          <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-1">
            <h4 className="font-bold text-emerald-400">1. Ordinary Least Squares (OLS) Linear Regression</h4>
            <p className="text-xs text-slate-400">
              Parametric model fitting <code className="text-slate-200">y(t) = β₀ + β₁t + ε</code> where <code className="text-slate-200">t</code> is elapsed years. Produces annual rates of change, two-sided p-values, t-statistics, and exact 95% confidence bands.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-1">
            <h4 className="font-bold text-emerald-400">2. Mann-Kendall Non-Parametric Trend Test</h4>
            <p className="text-xs text-slate-400">
              Evaluates monotonic trend direction without assuming normality or linearity. Implements tie-correction and continuity-corrected Z statistics evaluated at α = 0.05.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-1">
            <h4 className="font-bold text-emerald-400">3. Theil-Sen Robust Estimator</h4>
            <p className="text-xs text-slate-400">
              Computes the median of all pairwise observation slopes, offering high resistance to localized outliers, measurement spikes, and sensor irregularities.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-1">
            <h4 className="font-bold text-emerald-400">4. Seasonal Adjustment & Anomaly Decomposition</h4>
            <p className="text-xs text-slate-400">
              Subtracted 12-month calendar climatological baseline removes seasonal cycles, allowing detection of subtle underlying multi-year warming or drying trajectories.
            </p>
          </div>
        </div>
      </div>

      {/* Earth Science Datasets & Attribution */}
      <div className="glass-panel p-8 rounded-3xl space-y-6 border border-slate-800">
        <h2 className="text-xl font-bold text-white flex items-center gap-2">
          <Layers className="w-5 h-5 text-emerald-400" />
          Primary Earth Science Data Sources
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
          <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-2">
            <div className="flex justify-between items-center">
              <span className="font-bold text-white text-sm">NASA POWER</span>
              <span className="px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-400 font-mono">MERRA-2</span>
            </div>
            <p className="text-slate-400 leading-relaxed">
              Prediction Of Worldwide Energy Resources, managed by NASA Langley Research Center. Provides global meteorological and solar data calibrated against CERES and GPCP.
            </p>
            <a
              href="https://power.larc.nasa.gov/"
              target="_blank"
              rel="noopener noreferrer"
              className="text-emerald-400 font-semibold hover:underline inline-flex items-center gap-1"
            >
              NASA POWER Portal <ExternalLink className="w-3 h-3" />
            </a>
          </div>

          <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-2">
            <div className="flex justify-between items-center">
              <span className="font-bold text-white text-sm">NASADEM & WorldCover</span>
              <span className="px-2 py-0.5 rounded bg-sky-500/20 text-sky-400 font-mono">Context</span>
            </div>
            <p className="text-slate-400 leading-relaxed">
              NASADEM digital elevation model (SRTM reprocessing) and ESA WorldCover 2021 10m land cover classification serve strictly as geographic context.
            </p>
            <span className="text-[11px] text-slate-500 block">
              Static reference layers are never falsely presented as historical trends.
            </span>
          </div>
        </div>
      </div>

      {/* Scientific Integrity Pledge */}
      <div className="glass-panel p-8 rounded-3xl border border-emerald-500/30 bg-gradient-to-br from-emerald-950/20 to-slate-900/50 space-y-3">
        <h3 className="text-base font-bold text-white flex items-center gap-2">
          <ShieldCheck className="w-5 h-5 text-emerald-400" />
          Scientific Transparency & Non-Fabrication Guarantee
        </h3>
        <p className="text-xs text-slate-300 leading-relaxed">
          EarthTrend operates on strict scientific ethics: no measurements, observations, or statistical p-values are ever simulated or synthesized for live analyses. Non-significant findings are honestly reported as inconclusive evidence rather than misconstrued as proof of absence of change.
        </p>
      </div>
    </div>
  );
};
