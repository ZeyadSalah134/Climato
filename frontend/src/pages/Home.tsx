import React from 'react';
import { ArrowRight, Compass, Activity, Database, ShieldCheck, CheckCircle2, TrendingUp, BarChart3, MapPin } from 'lucide-react';

interface HomeProps {
  onNavigate: (page: string) => void;
  onExploreLocation: (name: string, lat: number, lon: number, variable: string) => void;
}

export const Home: React.FC<HomeProps> = ({ onNavigate, onExploreLocation }) => {
  const coreQuestions = [
    {
      q: '1. WHAT is changing?',
      ans: 'Near-surface air temperature, precipitation rates, and solar radiation sourced directly from NASA POWER reanalysis (MERRA-2).',
      icon: TrendingUp,
    },
    {
      q: '2. WHERE is it changing?',
      ans: 'Any coordinate globally, with high-density coverage across 30 verified stations in Egypt (Cairo, Alexandria, Nile Delta, Suez Canal).',
      icon: MapPin,
    },
    {
      q: '3. HOW MUCH is it changing?',
      ans: 'Calculates exact rates of change per year and per decade using Ordinary Least Squares and robust Theil-Sen estimators.',
      icon: BarChart3,
    },
    {
      q: '4. HOW does it change over time?',
      ans: 'Decomposes monthly observations from 2000 to 2025, removing seasonal oscillations to analyze baseline anomaly trajectories.',
      icon: Activity,
    },
    {
      q: '5. IS it statistically significant?',
      ans: 'Rigorous two-sided p-values and Mann-Kendall non-parametric monotonic trend tests evaluated at alpha = 0.05.',
      icon: ShieldCheck,
    },
  ];

  const presets = [
    {
      title: 'Cairo Central Warming Trend',
      region: 'Cairo / Giza, Egypt (30.04°N, 31.24°E)',
      variable: 'T2M',
      desc: '+0.31°C/decade warming detected over 2000-2025 (p < 0.001, Statistically Significant).',
      lat: 30.0444,
      lon: 31.2357,
    },
    {
      title: 'Alexandria Coastal Precipitation',
      region: 'Alexandria Coast, Egypt (31.20°N, 29.92°E)',
      variable: 'PRECTOTCORR',
      desc: 'Precipitation variability and seasonal anomaly shifts along the Mediterranean coast.',
      lat: 31.2001,
      lon: 29.9187,
    },
    {
      title: 'Nile Delta Solar Irradiance',
      region: 'Tanta / Gharbia (31.00°N, 31.25°E)',
      variable: 'ALLSKY_SFC_SW_DWN',
      desc: 'All-sky shortwave solar radiation dynamics in the agricultural heartland.',
      lat: 31.0,
      lon: 31.25,
    },
  ];

  return (
    <div className="space-y-16 py-8">
      {/* Hero Section */}
      <section className="relative overflow-hidden rounded-3xl p-8 sm:p-14 border border-emerald-500/20 bg-gradient-to-br from-navy-900 via-earth-950 to-navy-950 shadow-2xl">
        <div className="absolute top-0 right-0 -mr-20 -mt-20 w-96 h-96 bg-emerald-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute bottom-0 left-0 -ml-20 -mb-20 w-80 h-80 bg-teal-500/10 rounded-full blur-3xl pointer-events-none" />

        <div className="relative z-10 max-w-3xl space-y-6">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/25 text-emerald-400 text-xs font-semibold tracking-wide">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
            NASA Space Apps Challenge 2026 Project
          </div>

          <h1 className="text-4xl sm:text-6xl font-extrabold text-white tracking-tight leading-tight">
            Earth Intelligence & <br />
            <span className="bg-gradient-to-r from-emerald-400 via-teal-300 to-cyan-400 bg-clip-text text-transparent">
              Environmental Analytics
            </span>
          </h1>

          <p className="text-lg text-slate-300 leading-relaxed font-normal">
            EarthTrend transforms NASA Earth observations into scientifically verified, statistical environmental trend analysis. Powered by <strong className="text-white">28,080 verified historical observations</strong> (2000–2025) and live NASA POWER API integration.
          </p>

          <div className="flex flex-wrap items-center gap-4 pt-4">
            <button
              onClick={() => onNavigate('explorer')}
              className="flex items-center gap-2 px-6 py-3.5 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-navy-950 font-bold text-sm transition-all shadow-lg shadow-emerald-500/25 hover:shadow-emerald-500/40 hover:-translate-y-0.5"
            >
              <Compass className="w-5 h-5 stroke-[2.5]" />
              Open Interactive Earth Explorer
              <ArrowRight className="w-4 h-4" />
            </button>

            <button
              onClick={() => onNavigate('trend')}
              className="flex items-center gap-2 px-6 py-3.5 rounded-xl glass-panel hover:bg-slate-800/80 text-white font-semibold text-sm border border-slate-700 transition-all"
            >
              <Activity className="w-5 h-5 text-emerald-400" />
              View Trend Dashboard
            </button>
          </div>
        </div>
      </section>

      {/* 5 Core NASA Challenge Questions */}
      <section className="space-y-6">
        <div className="text-center max-w-2xl mx-auto space-y-2">
          <h2 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
            The 5 Core Scientific Questions
          </h2>
          <p className="text-slate-400 text-sm">
            EarthTrend answers each question through transparent mathematical models and empirical Earth observation data.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {coreQuestions.map((item, index) => {
            const Icon = item.icon;
            return (
              <div
                key={index}
                className="glass-panel glass-panel-hover p-6 rounded-2xl space-y-3 transition-all relative overflow-hidden group"
              >
                <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400 group-hover:scale-110 transition-transform">
                  <Icon className="w-5 h-5" />
                </div>
                <h3 className="text-base font-bold text-white tracking-tight">{item.q}</h3>
                <p className="text-sm text-slate-300 leading-relaxed">{item.ans}</p>
              </div>
            );
          })}
          <div className="glass-panel p-6 rounded-2xl flex flex-col justify-center items-start space-y-3 bg-gradient-to-br from-emerald-950/40 to-slate-900/60 border border-emerald-500/20">
            <span className="text-xs font-bold uppercase tracking-wider text-emerald-400">Strict Scientific Integrity</span>
            <p className="text-xs text-slate-300">
              Zero synthetic fabrication. Non-significant trends are objectively reported as inconclusive rather than falsely claimed as "proof of no climate change".
            </p>
            <button
              onClick={() => onNavigate('about')}
              className="text-xs text-emerald-400 font-semibold hover:underline inline-flex items-center gap-1"
            >
              Read full methodology &rarr;
            </button>
          </div>
        </div>
      </section>

      {/* Featured Investigation Presets */}
      <section className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-white tracking-tight">Verified Regional Presets</h2>
            <p className="text-sm text-slate-400">Instant analysis powered by the 2000-2025 Climato climate dataset.</p>
          </div>
          <button
            onClick={() => onNavigate('data')}
            className="text-xs font-semibold text-emerald-400 hover:text-emerald-300 flex items-center gap-1"
          >
            Explore all 30 stations &rarr;
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {presets.map((preset, index) => (
            <div
              key={index}
              onClick={() => onExploreLocation(preset.region, preset.lat, preset.lon, preset.variable)}
              className="glass-panel glass-panel-hover p-6 rounded-2xl space-y-4 cursor-pointer group transition-all"
            >
              <div className="flex items-center justify-between">
                <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                  {preset.variable}
                </span>
                <span className="text-xs text-slate-400 font-medium">2000–2025</span>
              </div>
              <div>
                <h3 className="text-lg font-bold text-white group-hover:text-emerald-300 transition-colors">
                  {preset.title}
                </h3>
                <p className="text-xs text-slate-400 mt-1">{preset.region}</p>
              </div>
              <p className="text-xs text-slate-300 leading-relaxed">{preset.desc}</p>
              <div className="pt-2 flex items-center text-xs font-bold text-emerald-400 group-hover:translate-x-1 transition-transform">
                Run Trend Analysis &rarr;
              </div>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
};
