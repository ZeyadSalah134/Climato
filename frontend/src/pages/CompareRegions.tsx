import React, { useState } from 'react';
import { GitCompare, Play, MapPin, ArrowRight, Layers, BarChart2 } from 'lucide-react';
import { InteractiveMap } from '../components/InteractiveMap';
import type { GeoPoint, VariableInfo, GridStation, CompareResponse } from '../types';

interface CompareRegionsProps {
  locationA: GeoPoint;
  onChangeLocationA: (loc: GeoPoint) => void;
  locationB: GeoPoint;
  onChangeLocationB: (loc: GeoPoint) => void;
  selectedVariable: string;
  onChangeVariable: (v: string) => void;
  startDate: string;
  endDate: string;
  variables: VariableInfo[];
  stations: GridStation[];
  onRunCompare: () => Promise<CompareResponse>;
  compareResult: CompareResponse | null;
  isComparing: boolean;
}

export const CompareRegions: React.FC<CompareRegionsProps> = ({
  locationA,
  onChangeLocationA,
  locationB,
  onChangeLocationB,
  selectedVariable,
  onChangeVariable,
  startDate,
  endDate,
  variables,
  stations,
  onRunCompare,
  compareResult,
  isComparing,
}) => {
  const currentVar = variables.find((v) => v.id === selectedVariable) || variables[0];

  return (
    <div className="space-y-8 py-4">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-extrabold text-white tracking-tight">Compare Regions</h1>
        <p className="text-sm text-slate-400">
          Compare environmental trends and rate of change between two geographical regions over the same historical period.
        </p>
      </div>

      {/* Location Picker & Variable Controls */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        <div className="lg:col-span-8 space-y-6">
          <div className="glass-panel p-4 rounded-3xl">
            <InteractiveMap
              selectedLocation={locationA}
              onSelectLocation={onChangeLocationA}
              compareLocation={locationB}
              onSelectCompareLocation={onChangeLocationB}
              stations={stations}
              isCompareMode={true}
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Location A Card */}
            <div className="glass-panel p-5 rounded-2xl border-l-4 border-l-emerald-500 space-y-2">
              <span className="text-[11px] font-bold text-emerald-400 uppercase tracking-wider">Location A (Primary)</span>
              <h3 className="text-base font-bold text-white">{locationA.name || 'Location A'}</h3>
              <p className="text-xs font-mono text-slate-400">
                {locationA.latitude.toFixed(4)}°N, {locationA.longitude.toFixed(4)}°E
              </p>
            </div>

            {/* Location B Card */}
            <div className="glass-panel p-5 rounded-2xl border-l-4 border-l-sky-500 space-y-2">
              <span className="text-[11px] font-bold text-sky-400 uppercase tracking-wider">Location B (Comparison)</span>
              <h3 className="text-base font-bold text-white">{locationB.name || 'Location B'}</h3>
              <p className="text-xs font-mono text-slate-400">
                {locationB.latitude.toFixed(4)}°N, {locationB.longitude.toFixed(4)}°E
              </p>
            </div>
          </div>
        </div>

        {/* Configuration Panel */}
        <div className="lg:col-span-4 space-y-6">
          <div className="glass-panel p-6 rounded-3xl space-y-6">
            <h2 className="text-lg font-bold text-white flex items-center gap-2 pb-3 border-b border-slate-800">
              <GitCompare className="w-5 h-5 text-emerald-400" />
              Comparison Setup
            </h2>

            <div className="space-y-2">
              <label className="text-xs font-bold text-slate-300 uppercase tracking-wider">
                Target Variable
              </label>
              <select
                value={selectedVariable}
                onChange={(e) => onChangeVariable(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3.5 py-2.5 text-sm text-white focus:outline-none focus:border-emerald-500"
              >
                {variables.map((v) => (
                  <option key={v.id} value={v.id}>
                    {v.display_name} ({v.units})
                  </option>
                ))}
              </select>
            </div>

            <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-1 text-xs text-slate-300">
              <span className="font-semibold text-white block">Compatible Period</span>
              <span>{startDate} to {endDate}</span>
              <p className="text-[11px] text-slate-500 pt-1">
                Both locations are sampled synchronously on the monthly NASA POWER grid.
              </p>
            </div>

            <button
              onClick={onRunCompare}
              disabled={isComparing}
              className="w-full py-4 rounded-2xl bg-gradient-to-r from-emerald-500 to-sky-500 hover:from-emerald-400 hover:to-sky-400 text-navy-950 font-extrabold text-sm transition-all shadow-lg shadow-emerald-500/20 flex items-center justify-center gap-2 disabled:opacity-50"
            >
              {isComparing ? 'Comparing Trends...' : 'Execute Regional Comparison'}
            </button>
          </div>
        </div>
      </div>

      {/* Comparison Results */}
      {compareResult && (
        <div className="space-y-6 pt-4">
          <div className="glass-panel p-6 rounded-3xl border border-slate-800 space-y-4">
            <h2 className="text-xl font-extrabold text-white">Descriptive Comparison Summary</h2>
            <p className="text-sm text-slate-200 leading-relaxed">
              {compareResult.comparison.summary}
            </p>
            <p className="text-xs text-slate-400 border-t border-slate-800 pt-3">
              <strong>Scientific Note:</strong> {compareResult.comparison.note}
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Location A Metrics */}
            <div className="glass-panel p-6 rounded-3xl space-y-4 border-t-4 border-t-emerald-500">
              <div className="flex justify-between items-center">
                <h3 className="font-bold text-white text-lg">{compareResult.location_a.request.location.name}</h3>
                <span className="text-xs font-mono px-2 py-0.5 rounded bg-emerald-500/15 text-emerald-400">Location A</span>
              </div>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between py-1.5 border-b border-slate-800">
                  <span className="text-slate-400">OLS Slope / year:</span>
                  <span className="font-mono font-bold text-white">
                    {compareResult.location_a.ols?.slope_per_year.toFixed(4)} {currentVar.units}/yr
                  </span>
                </div>
                <div className="flex justify-between py-1.5 border-b border-slate-800">
                  <span className="text-slate-400">OLS Slope / decade:</span>
                  <span className="font-mono font-bold text-white">
                    {compareResult.location_a.ols?.slope_per_decade.toFixed(3)} {currentVar.units}/decade
                  </span>
                </div>
                <div className="flex justify-between py-1.5 border-b border-slate-800">
                  <span className="text-slate-400">Statistical Significance:</span>
                  <span className={`font-bold ${compareResult.location_a.ols?.significant ? 'text-emerald-400' : 'text-slate-400'}`}>
                    {compareResult.location_a.ols?.significant ? 'Significant (p < 0.05)' : 'Not Significant'}
                  </span>
                </div>
              </div>
            </div>

            {/* Location B Metrics */}
            <div className="glass-panel p-6 rounded-3xl space-y-4 border-t-4 border-t-sky-500">
              <div className="flex justify-between items-center">
                <h3 className="font-bold text-white text-lg">{compareResult.location_b.request.location.name}</h3>
                <span className="text-xs font-mono px-2 py-0.5 rounded bg-sky-500/15 text-sky-400">Location B</span>
              </div>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between py-1.5 border-b border-slate-800">
                  <span className="text-slate-400">OLS Slope / year:</span>
                  <span className="font-mono font-bold text-white">
                    {compareResult.location_b.ols?.slope_per_year.toFixed(4)} {currentVar.units}/yr
                  </span>
                </div>
                <div className="flex justify-between py-1.5 border-b border-slate-800">
                  <span className="text-slate-400">OLS Slope / decade:</span>
                  <span className="font-mono font-bold text-white">
                    {compareResult.location_b.ols?.slope_per_decade.toFixed(3)} {currentVar.units}/decade
                  </span>
                </div>
                <div className="flex justify-between py-1.5 border-b border-slate-800">
                  <span className="text-slate-400">Statistical Significance:</span>
                  <span className={`font-bold ${compareResult.location_b.ols?.significant ? 'text-sky-400' : 'text-slate-400'}`}>
                    {compareResult.location_b.ols?.significant ? 'Significant (p < 0.05)' : 'Not Significant'}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
