import React, { useState } from 'react';
import { Database, Download, FileSpreadsheet, Play, Search, MapPin, CheckCircle2 } from 'lucide-react';
import type { GridStation, VerifiedDatasetResponse } from '../types';

interface DataExplorerProps {
  datasetInfo: VerifiedDatasetResponse | null;
  onSelectStationToAnalyze: (station: GridStation, variable: string) => void;
}

export const DataExplorer: React.FC<DataExplorerProps> = ({
  datasetInfo,
  onSelectStationToAnalyze,
}) => {
  const [filterQuery, setFilterQuery] = useState('');
  const [selectedVar, setSelectedVar] = useState('T2M');

  const stations = datasetInfo?.stations || [];
  const filtered = stations.filter((s) =>
    s.name.toLowerCase().includes(filterQuery.toLowerCase()) ||
    s.point_id.includes(filterQuery)
  );

  return (
    <div className="space-y-8 py-4">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-extrabold text-white tracking-tight">Data Explorer</h1>
          <p className="text-sm text-slate-400">
            Browse and inspect the 28,080 verified NASA POWER climate observations across 30 regional stations in Egypt.
          </p>
        </div>

        {/* Download Deliverable Datasets */}
        <div className="flex items-center gap-3">
          <a
            href="/climate_power_monthly_2000-2025.csv"
            download
            className="px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-bold border border-slate-700 flex items-center gap-2 transition-colors shadow-sm"
          >
            <Download className="w-3.5 h-3.5 text-emerald-400" />
            Download CSV (28k rows)
          </a>
          <a
            href="/climate_power_monthly_2000-2025.xlsx"
            download
            className="px-4 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold flex items-center gap-2 transition-colors shadow-lg shadow-emerald-500/20"
          >
            <FileSpreadsheet className="w-3.5 h-3.5" />
            Download Excel Deliverable
          </a>
        </div>
      </div>

      {/* Dataset Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="glass-panel p-5 rounded-2xl">
          <span className="text-xs font-semibold text-slate-400 uppercase">Total Observations</span>
          <div className="text-2xl font-extrabold font-mono text-white mt-1">28,080</div>
          <span className="text-xs text-emerald-400 mt-1 block">100% Complete & Verified</span>
        </div>

        <div className="glass-panel p-5 rounded-2xl">
          <span className="text-xs font-semibold text-slate-400 uppercase">Temporal Coverage</span>
          <div className="text-2xl font-extrabold font-mono text-white mt-1">2000 – 2025</div>
          <span className="text-xs text-slate-400 mt-1 block">312 Months (26 Years)</span>
        </div>

        <div className="glass-panel p-5 rounded-2xl">
          <span className="text-xs font-semibold text-slate-400 uppercase">Verified Stations</span>
          <div className="text-2xl font-extrabold font-mono text-white mt-1">{stations.length} Grid Points</div>
          <span className="text-xs text-slate-400 mt-1 block">Egypt & Nile Delta Region</span>
        </div>

        <div className="glass-panel p-5 rounded-2xl">
          <span className="text-xs font-semibold text-slate-400 uppercase">Core Variables</span>
          <div className="text-2xl font-extrabold font-mono text-white mt-1">3 Parameters</div>
          <span className="text-xs text-slate-400 mt-1 block">T2M, PRECTOTCORR, SW_DWN</span>
        </div>
      </div>

      {/* Station List Table */}
      <div className="glass-panel rounded-3xl overflow-hidden border border-slate-800">
        <div className="p-6 border-b border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="relative flex-1 max-w-md">
            <Search className="w-4 h-4 absolute left-3.5 top-3.5 text-slate-400" />
            <input
              type="text"
              value={filterQuery}
              onChange={(e) => setFilterQuery(e.target.value)}
              placeholder="Filter stations (e.g. Cairo, Alexandria, Suez, Delta)..."
              className="w-full bg-slate-900 border border-slate-700/80 rounded-xl pl-10 pr-4 py-2.5 text-sm text-white placeholder-slate-400 focus:outline-none focus:border-emerald-500"
            />
          </div>

          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-400 font-medium">Quick Analyze Variable:</span>
            <select
              value={selectedVar}
              onChange={(e) => setSelectedVar(e.target.value)}
              className="bg-slate-900 border border-slate-700 text-xs font-bold text-white rounded-xl px-3 py-2"
            >
              <option value="T2M">T2M (Air Temperature)</option>
              <option value="PRECTOTCORR">PRECTOTCORR (Precipitation)</option>
              <option value="ALLSKY_SFC_SW_DWN">SW_DWN (Solar Radiation)</option>
            </select>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-900/80 text-xs font-bold uppercase tracking-wider text-slate-400 border-b border-slate-800">
              <tr>
                <th className="py-4 px-6">Station / Region Name</th>
                <th className="py-4 px-6">Grid Point ID</th>
                <th className="py-4 px-6">Latitude</th>
                <th className="py-4 px-6">Longitude</th>
                <th className="py-4 px-6 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {filtered.map((st) => (
                <tr key={st.point_id} className="hover:bg-slate-800/40 transition-colors">
                  <td className="py-4 px-6 font-semibold text-white flex items-center gap-2">
                    <MapPin className="w-4 h-4 text-emerald-400 shrink-0" />
                    {st.name}
                  </td>
                  <td className="py-4 px-6 font-mono text-xs text-slate-300">{st.point_id}</td>
                  <td className="py-4 px-6 font-mono text-xs text-slate-300">{st.latitude.toFixed(3)}°N</td>
                  <td className="py-4 px-6 font-mono text-xs text-slate-300">{st.longitude.toFixed(3)}°E</td>
                  <td className="py-4 px-6 text-right">
                    <button
                      onClick={() => onSelectStationToAnalyze(st, selectedVar)}
                      className="px-3.5 py-1.5 rounded-lg bg-emerald-500/15 hover:bg-emerald-500 text-emerald-400 hover:text-navy-950 font-bold text-xs border border-emerald-500/30 transition-all inline-flex items-center gap-1"
                    >
                      <Play className="w-3 h-3 fill-current" />
                      Analyze Trend
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
