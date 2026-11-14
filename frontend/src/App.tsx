import React, { useState, useEffect } from 'react';
import { Navbar } from './components/Navbar';
import { Home } from './pages/Home';
import { EarthExplorer } from './pages/EarthExplorer';
import { TrendAnalysis } from './pages/TrendAnalysis';
import { CompareRegions } from './pages/CompareRegions';
import { DataExplorer } from './pages/DataExplorer';
import { About } from './pages/About';
import {
  fetchHealth,
  fetchVariables,
  fetchVerifiedDataset,
  runTrendAnalysis,
  runCompareAnalysis,
  searchLocations,
} from './api/client';
import type {
  GeoPoint,
  VariableInfo,
  GridStation,
  TrendAnalysisResponse,
  CompareResponse,
  VerifiedDatasetResponse,
} from './types';

export const App: React.FC = () => {
  const [currentPage, setCurrentPage] = useState('home');
  const [backendOnline, setBackendOnline] = useState(false);
  const [variables, setVariables] = useState<VariableInfo[]>([]);
  const [datasetInfo, setDatasetInfo] = useState<VerifiedDatasetResponse | null>(null);

  // Active Analysis State
  const [selectedLocation, setSelectedLocation] = useState<GeoPoint>({
    latitude: 30.0444,
    longitude: 31.2357,
    name: 'Cairo, Egypt',
    country: 'Egypt',
    region: 'Africa',
  });

  const [compareLocation, setCompareLocation] = useState<GeoPoint>({
    latitude: 31.2001,
    longitude: 29.9187,
    name: 'Alexandria, Egypt',
    country: 'Egypt',
    region: 'Africa',
  });

  const [selectedVariable, setSelectedVariable] = useState('T2M');
  const [startDate, setStartDate] = useState('2000-01-01');
  const [endDate, setEndDate] = useState('2025-12-01');
  const [seasonalAdjustment, setSeasonalAdjustment] = useState(true);
  const [alpha, setAlpha] = useState(0.05);

  const [trendResult, setTrendResult] = useState<TrendAnalysisResponse | null>(null);
  const [compareResult, setCompareResult] = useState<CompareResponse | null>(null);

  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isComparing, setIsComparing] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Initialize application data
  useEffect(() => {
    async function loadInitialData() {
      try {
        const health = await fetchHealth();
        setBackendOnline(health.status === 'ok' || health.status === 'degraded');
      } catch {
        setBackendOnline(false);
      }

      try {
        const vars = await fetchVariables();
        if (vars && vars.length > 0) setVariables(vars);
      } catch (e) {
        console.error('Failed to load variables', e);
      }

      try {
        const ds = await fetchVerifiedDataset();
        setDatasetInfo(ds);
      } catch (e) {
        console.error('Failed to load verified dataset stations', e);
      }
    }

    loadInitialData();
  }, []);

  // Execute Trend Analysis
  const handleRunAnalysis = async (customParams?: {
    location?: GeoPoint;
    variable?: string;
    start?: string;
    end?: string;
  }) => {
    setIsAnalyzing(true);
    setErrorMessage(null);

    const loc = customParams?.location || selectedLocation;
    const variable = customParams?.variable || selectedVariable;
    const start = customParams?.start || startDate;
    const end = customParams?.end || endDate;

    try {
      const res = await runTrendAnalysis({
        variable,
        location: loc,
        start_date: start,
        end_date: end,
        seasonal_adjustment: seasonalAdjustment,
        alpha,
      });
      setTrendResult(res);
      setCurrentPage('trend');
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to complete trend analysis.');
    } finally {
      setIsAnalyzing(false);
    }
  };

  // Execute Comparison
  const handleRunCompare = async (): Promise<CompareResponse> => {
    setIsComparing(true);
    setErrorMessage(null);
    try {
      const res = await runCompareAnalysis({
        variable: selectedVariable,
        location_a: selectedLocation,
        location_b: compareLocation,
        start_date: startDate,
        end_date: endDate,
        seasonal_adjustment: seasonalAdjustment,
      });
      setCompareResult(res);
      return res;
    } catch (err: any) {
      setErrorMessage(err.message || 'Comparison request failed.');
      throw err;
    } finally {
      setIsComparing(false);
    }
  };

  // Preset explorer handler
  const handlePresetExplore = (name: string, lat: number, lon: number, variable: string) => {
    const loc: GeoPoint = { latitude: lat, longitude: lon, name };
    setSelectedLocation(loc);
    setSelectedVariable(variable);
    handleRunAnalysis({ location: loc, variable });
  };

  // Direct station handler from Data Explorer
  const handleStationExplore = (station: GridStation, variable: string) => {
    const loc: GeoPoint = {
      latitude: station.latitude,
      longitude: station.longitude,
      name: station.name,
    };
    setSelectedLocation(loc);
    setSelectedVariable(variable);
    handleRunAnalysis({ location: loc, variable });
  };

  const stations = datasetInfo?.stations || [];

  return (
    <div className="min-h-screen flex flex-col bg-navy-950 text-slate-100">
      <Navbar
        currentPage={currentPage}
        onNavigate={setCurrentPage}
        backendOnline={backendOnline}
      />

      {/* Global Error Banner */}
      {errorMessage && (
        <div className="bg-rose-950/80 border-b border-rose-800 text-rose-200 px-4 py-3 text-xs flex items-center justify-between">
          <div className="max-w-7xl mx-auto flex items-center gap-2">
            <span className="font-bold">Error:</span>
            <span>{errorMessage}</span>
          </div>
          <button
            onClick={() => setErrorMessage(null)}
            className="text-rose-400 hover:text-white font-bold text-sm"
          >
            ×
          </button>
        </div>
      )}

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 pb-16">
        {currentPage === 'home' && (
          <Home
            onNavigate={setCurrentPage}
            onExploreLocation={handlePresetExplore}
          />
        )}

        {currentPage === 'explorer' && (
          <EarthExplorer
            selectedLocation={selectedLocation}
            onSelectLocation={setSelectedLocation}
            selectedVariable={selectedVariable}
            onSelectVariable={setSelectedVariable}
            startDate={startDate}
            onSelectStartDate={setStartDate}
            endDate={endDate}
            onSelectEndDate={setEndDate}
            seasonalAdjustment={seasonalAdjustment}
            onToggleSeasonal={setSeasonalAdjustment}
            alpha={alpha}
            onSelectAlpha={setAlpha}
            variables={variables}
            stations={stations}
            onStartAnalysis={() => handleRunAnalysis()}
            isAnalyzing={isAnalyzing}
            onSearchQuery={searchLocations}
          />
        )}

        {currentPage === 'trend' && (
          <TrendAnalysis
            data={trendResult}
            onRefresh={() => handleRunAnalysis()}
            onNavigateToExplorer={() => setCurrentPage('explorer')}
          />
        )}

        {currentPage === 'compare' && (
          <CompareRegions
            locationA={selectedLocation}
            onChangeLocationA={setSelectedLocation}
            locationB={compareLocation}
            onChangeLocationB={setCompareLocation}
            selectedVariable={selectedVariable}
            onChangeVariable={setSelectedVariable}
            startDate={startDate}
            endDate={endDate}
            variables={variables}
            stations={stations}
            onRunCompare={handleRunCompare}
            compareResult={compareResult}
            isComparing={isComparing}
          />
        )}

        {currentPage === 'data' && (
          <DataExplorer
            datasetInfo={datasetInfo}
            onSelectStationToAnalyze={handleStationExplore}
          />
        )}

        {currentPage === 'about' && <About />}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-900 bg-navy-950 py-8 text-xs text-slate-500">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <span className="font-extrabold text-slate-300">EarthTrend</span>
            <span>&copy; 2026 NASA Space Apps Challenge Submission</span>
          </div>
          <div className="flex items-center gap-6 text-slate-400">
            <span>NASA POWER MERRA-2 Reanalysis</span>
            <span>NASADEM & WorldCover Context</span>
            <a
              href="https://github.com/ZeyadSalah134/Climato"
              target="_blank"
              rel="noopener noreferrer"
              className="text-emerald-400 hover:underline"
            >
              GitHub Repository
            </a>
          </div>
        </div>
      </footer>
    </div>
  );
};
