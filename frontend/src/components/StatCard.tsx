import React from 'react';
import { LucideIcon } from 'lucide-react';

interface StatCardProps {
  label: string;
  value: string | number;
  subValue?: string;
  unit?: string;
  icon?: LucideIcon;
  badge?: {
    text: string;
    variant: 'success' | 'warning' | 'info' | 'neutral';
  };
  tooltip?: string;
}

export const StatCard: React.FC<StatCardProps> = ({
  label,
  value,
  subValue,
  unit,
  icon: Icon,
  badge,
  tooltip,
}) => {
  const badgeColors = {
    success: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30',
    warning: 'bg-amber-500/15 text-amber-400 border-amber-500/30',
    info: 'bg-sky-500/15 text-sky-400 border-sky-500/30',
    neutral: 'bg-slate-700/30 text-slate-400 border-slate-700/50',
  };

  return (
    <div className="glass-panel glass-panel-hover p-5 rounded-2xl relative overflow-hidden transition-all duration-200">
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">{label}</span>
        {Icon && <Icon className="w-4 h-4 text-emerald-400" />}
      </div>

      <div className="flex items-baseline gap-2 mb-1">
        <span className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight font-mono">{value}</span>
        {unit && <span className="text-xs font-semibold text-slate-400">{unit}</span>}
      </div>

      <div className="flex items-center justify-between text-xs mt-2">
        {subValue && <span className="text-slate-400 font-medium">{subValue}</span>}
        {badge && (
          <span className={`px-2 py-0.5 rounded-full text-[11px] font-bold border ${badgeColors[badge.variant]}`}>
            {badge.text}
          </span>
        )}
      </div>

      {tooltip && (
        <p className="text-[11px] text-slate-500 mt-2 border-t border-slate-800/60 pt-1.5">{tooltip}</p>
      )}
    </div>
  );
};
