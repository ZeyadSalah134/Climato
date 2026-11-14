import React from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js';
import { Line } from 'react-chartjs-2';
import type { TrendAnalysisResponse } from '../types';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

interface TimeSeriesChartProps {
  data: TrendAnalysisResponse;
  showConfidenceInterval?: boolean;
}

export const TimeSeriesChart: React.FC<TimeSeriesChartProps> = ({
  data,
  showConfidenceInterval = true,
}) => {
  const points = data.trend_line || [];
  const labels = points.map((p) => p.date);
  const observedValues = points.map((p) => p.observed ?? null);
  const fittedValues = points.map((p) => p.fitted);
  const lowerBounds = points.map((p) => p.lower ?? p.fitted);
  const upperBounds = points.map((p) => p.upper ?? p.fitted);

  const units = data.provenance.units || 'units';

  const datasets: any[] = [
    {
      label: 'Observed Values',
      data: observedValues,
      borderColor: '#10b981', // emerald-500
      backgroundColor: 'rgba(16, 185, 129, 0.25)',
      pointRadius: points.length > 100 ? 1.5 : 3,
      pointHoverRadius: 5,
      borderWidth: 1.5,
      tension: 0.1,
    },
    {
      label: `OLS Fitted Trend (${data.ols?.slope_per_year.toFixed(4) || 0} ${units}/yr)`,
      data: fittedValues,
      borderColor: '#f59e0b', // amber-500
      backgroundColor: 'transparent',
      borderWidth: 2.5,
      borderDash: [5, 4],
      pointRadius: 0,
    },
  ];

  if (showConfidenceInterval && data.ols) {
    datasets.push({
      label: 'Upper 95% CI',
      data: upperBounds,
      borderColor: 'rgba(56, 189, 248, 0.4)',
      backgroundColor: 'transparent',
      borderWidth: 1,
      borderDash: [2, 2],
      pointRadius: 0,
      fill: false,
    });
    datasets.push({
      label: '95% Confidence Band',
      data: lowerBounds,
      borderColor: 'rgba(56, 189, 248, 0.4)',
      backgroundColor: 'rgba(56, 189, 248, 0.08)',
      borderWidth: 1,
      borderDash: [2, 2],
      pointRadius: 0,
      fill: '-1', // fill between lower and upper
    });
  }

  const chartData = {
    labels,
    datasets,
  };

  const options: any = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: {
      mode: 'index',
      intersect: false,
    },
    plugins: {
      legend: {
        position: 'top' as const,
        labels: {
          color: '#cbd5e1',
          font: { family: 'Inter', size: 12 },
          boxWidth: 14,
          padding: 16,
        },
      },
      tooltip: {
        backgroundColor: '#0f172a',
        titleColor: '#38bdf8',
        bodyColor: '#e2e8f0',
        borderColor: '#334155',
        borderWidth: 1,
        padding: 10,
        callbacks: {
          label: (context: any) => {
            const val = context.parsed.y;
            return ` ${context.dataset.label}: ${val !== null ? val.toFixed(3) : 'n/a'} ${units}`;
          },
        },
      },
    },
    scales: {
      x: {
        grid: { color: 'rgba(51, 65, 85, 0.3)' },
        ticks: {
          color: '#94a3b8',
          maxTicksLimit: 12,
          font: { family: 'JetBrains Mono', size: 10 },
        },
      },
      y: {
        grid: { color: 'rgba(51, 65, 85, 0.3)' },
        ticks: {
          color: '#94a3b8',
          font: { family: 'JetBrains Mono', size: 11 },
        },
        title: {
          display: true,
          text: `${data.provenance.variable_name} (${units})`,
          color: '#cbd5e1',
          font: { family: 'Inter', size: 12, weight: 'bold' },
        },
      },
    },
  };

  return (
    <div className="w-full h-[400px]">
      <Line data={chartData} options={options} />
    </div>
  );
};
