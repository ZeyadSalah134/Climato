import React, { useState } from 'react';
import { Search, MapPin, Play, Calendar, Sliders, Sparkles, AlertCircle, Database } from 'lucide-react';
import { InteractiveMap } from '../components/InteractiveMap';
import type { GeoPoint, VariableInfo, GridStation } from '../types';

interface EarthExplorerProps {
  selectedLocation: GeoPoint;
  onSelectLocation: (loc: GeoPoint) => void;
  selectedVariable: string;
  onSelectVariable: (varId: string) => void;
  startDate: string;
  onSelectStartDate: (d: string) => void;
  endDate: string;
  onSelectEndDate: (d: string) => void;
  seasonalAdjustment: boolean;
  onToggleSeasonal: (val: boolean) => void;
  alpha: number;
  onSelectAlpha: (val: number) => void;
  variables: VariableInfo[];
  stations: GridStation[];
  onStartAnalysis: () => void;
  isAnalyzing: boolean;
  onSearchQuery: (query: string) => Promise<GeoPoint[]>;
}

export const EarthExplorer: React.FC<EarthExplorerProps> = ({
  selectedLocation,
  onSelectLocation,
  selectedVariable,
  onSelectVariable,
  startDate,
  onSelectStartDate,
  endDate,
  onSelectEndDate,
  seasonalAdjustment,
  onToggleSeasonal,
  alpha,
  onSelectAlpha,
  variables,
  stations,
  onStartAnalysis,
  isAnalyzing,
  onSearchQuery,
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<GeoPoint[]>([]);
  const [isSearching, setIsSearching] = useState(false);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;
    setIsSearching(true);
    try {
      const results = await onSearchQuery(searchQuery);
      setSearchResults(results);
    } finally {
      setIsSearching(false);
    }
  };

  const currentVar = variables.find((v) => v.id === selectedVariable) || variables[0];

  return (
    <div className="space-y-8 py-4">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-extrabold text-white tracking-tight">Earth Explorer</h1>
          <p className="text-sm text-slate-400">
            Select a geographical location on the map, choose your environmental variable and date range, and execute verified statistical trend analysis.
          </p>
        </div>
        <div className="flex items-center gap-2 self-start md:self-auto">
          <span className="px-3 py-1 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/25 text-xs font-semibold flex items-center gap-1.5">
            <Database className="w-3.5 h-3.5" />
            30 Verified NASA Stations Active
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Left Column: Interactive Map & Location Search */}
        <div className="lg:col-span-8 space-y-6">
          {/* Location Search Bar */}
          <div className="glass-panel p-3 rounded-2xl">
            <form onSubmit={handleSearch} className="flex gap-2">
              <div className="relative flex-1">
                <Search className="w-4 h-4 absolute left-3.5 top-3.5 text-slate-400" />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search city or region (e.g. Cairo, Alexandria, Damietta, Nairobi)..."
                  className="w-full bg-slate-900/80 border border-slate-700/80 rounded-xl pl-10 pr-4 py-2.5 text-sm text-white placeholder-slate-400 focus:outline-none focus:border-emerald-500 transition-colors"
                />
              </div>
              <button
                type="submit"
                disabled={isSearching}
                className="px-5 py-2.5 bg-slate-800 hover:bg-slate-700 text-white text-xs font-bold rounded-xl border border-slate-700 transition-all flex items-center gap-1.5"
              >
                {isSearching ? 'Searching...' : 'Search'}
              </button>
            </form>

            {/* Search Results Dropdown */}
            {searchResults.length > 0 && (
              <div className="mt-3 pt-3 border-t border-slate-800/80 space-y-1 max-h-48 overflow-y-auto">
                <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block mb-1">
                  Search Results
                </span>
                {searchResults.map((pt, idx) => (
                  <div
                    key={idx}
                    onClick={() => {
                      onSelectLocation(pt);
                      setSearchResults([]);
                      setSearchQuery(pt.name || '');
                    }}
                    className="flex items-center justify-between p-2 rounded-lg hover:bg-slate-800/80 cursor-pointer text-xs transition-colors"
                  >
                    <span className="text-white font-medium">{pt.name}</span>
                    <span className="text-slate-400 font-mono">
                      {pt.latitude.toFixed(2)}°, {pt.longitude.toFixed(2)}°
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Leaflet Interactive Map */}
          <div className="glass-panel p-4 rounded-3xl">
            <InteractiveMap
              selectedLocation={selectedLocation}
              onSelectLocation={onSelectLocation}
              stations={stations}
            />
          </div>

          {/* Selected Coordinate Details */}
          <div className="glass-panel p-5 rounded-2xl flex flex-wrap items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
                <MapPin className="w-5 h-5" />
              </div>
              <div>
                <span className="text-xs text-slate-400 uppercase tracking-wider font-semibold">Active Location Target</span>
                <h3 className="text-base font-bold text-white">{selectedLocation.name || 'Custom Coordinate Point'}</h3>
                <span className="text-xs font-mono text-emerald-400 font-semibold">
                  {selectedLocation.latitude.toFixed(4)}°N, {selectedLocation.longitude.toFixed(4)}°E
                </span>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <span className="text-xs text-slate-400">Grid alignment:</span>
              <span className="px-2.5 py-1 rounded-md bg-slate-800 border border-slate-700 text-xs font-mono text-slate-200">
                ~0.5° × 0.625° MERRA-2
              </span>
            </div>
          </div>
        </div>

        {/* Right Column: Analysis Configuration Panel */}
        <div className="lg:col-span-4 space-y-6">
          <div className="glass-panel p-6 rounded-3xl space-y-6">
            <h2 className="text-lg font-bold text-white flex items-center gap-2 pb-3 border-b border-slate-800">
              <Sliders className="w-5 h-5 text-emerald-400" />
              Analysis Settings
            </h2>

            {/* Variable Selection */}
            <div className="space-y-2">
              <label className="text-xs font-bold text-slate-300 uppercase tracking-wider">
                Environmental Variable
              </label>
              <select
                value={selectedVariable}
                onChange={(e) => onSelectVariable(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3.5 py-2.5 text-sm text-white focus:outline-none focus:border-emerald-500"
              >
                {variables.map((v) => (
                  <option key={v.id} value={v.id}>
                    {v.display_name} ({v.units}) — {v.code}
                  </option>
                ))}
              </select>
              {currentVar && (
                <p className="text-[11px] text-slate-400 leading-relaxed pt-1">
                  {currentVar.description}
                </p>
              )}
            </div>

            {/* Date Range Selector */}
            <div className="space-y-3">
              <label className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
                <Calendar className="w-4 h-4 text-emerald-400" />
                Historical Time Range
              </label>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <span className="text-[11px] text-slate-400 block mb-1">Start Date</span>
                  <input
                    type="date"
                    value={startDate}
                    onChange={(e) => onSelectStartDate(e.target.value)}
                    min="1981-01-01"
                    max={endDate}
                    className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-emerald-500 font-mono"
                  />
                </div>
                <div>
                  <span className="text-[11px] text-slate-400 block mb-1">End Date</span>
                  <input
                    type="date"
                    value={endDate}
                    onChange={(e) => onSelectEndDate(e.target.value)}
                    min={startDate}
                    max="2025-12-01"
                    className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-emerald-500 font-mono"
                  />
                </div>
              </div>
              <span className="text-[11px] text-slate-500">
                Verified dataset spans 2000-01 to 2025-12 (312 months).
              </span>
            </div>

            {/* Seasonal Adjustment Toggle */}
            <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 space-y-2">
              <div className="flex items-center justify-between">
                <div>
                  <span className="text-xs font-bold text-white block">Seasonal Adjustment</span>
                  <span className="text-[11px] text-slate-400">Removes 12-month cyclical noise</span>
                </div>
                <button
                  type="button"
                  onClick={() => onToggleSeasonal(!seasonalAdjustment)}
                  className={`w-11 h-6 flex items-center rounded-full p-1 transition-colors ${
                    seasonalAdjustment ? 'bg-emerald-500' : 'bg-slate-700'
                  }`}
                >
                  <div
                    className={`bg-white w-4 h-4 rounded-full shadow-md transform transition-transform ${
                      seasonalAdjustment ? 'translate-x-5' : 'translate-x-0'
                    }`}
                  />
                </button>
              </div>
            </div>

            {/* Significance Alpha Threshold */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-slate-300 uppercase tracking-wider">Significance (α)</span>
                <span className="text-xs font-mono text-emerald-400 font-bold">{alpha} (95% CI)</span>
              </div>
              <div className="grid grid-cols-3 gap-2">
                {[0.01, 0.05, 0.1].map((val) => (
                  <button
                    key={val}
                    type="button"
                    onClick={() => onSelectAlpha(val)}
                    className={`py-1.5 rounded-lg text-xs font-semibold border transition-all ${
                      alpha === val
                        ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/50'
                        : 'bg-slate-900 text-slate-400 border-slate-800 hover:border-slate-700'
                    }`}
                  >
                    α = {val}
                  </button>
                ))}
              </div>
            </div>

            {/* Run Analysis Action Button */}
            <button
              onClick={onStartAnalysis}
              disabled={isAnalyzing}
              className="w-full py-4 rounded-2xl bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-400 hover:to-teal-400 text-navy-950 font-extrabold text-sm transition-all shadow-lg shadow-emerald-500/25 hover:shadow-emerald-500/40 hover:-translate-y-0.5 flex items-center justify-center gap-2 disabled:opacity-50"
            >
              {isAnalyzing ? (
                <>
                  <span className="w-4 h-4 border-2 border-navy-950 border-t-transparent rounded-full animate-spin" />
                  Calculating NASA Statistics...
                </>
              ) : (
                <>
                  <Play className="w-4 h-4 fill-current" />
                  Run Statistical Trend Analysis
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
