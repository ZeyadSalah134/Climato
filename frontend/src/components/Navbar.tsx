import React from 'react';
import { Globe2, Activity, GitCompare, Database, Info, Compass, ShieldCheck } from 'lucide-react';

interface NavbarProps {
  currentPage: string;
  onNavigate: (page: string) => void;
  backendOnline: boolean;
}

export const Navbar: React.FC<NavbarProps> = ({ currentPage, onNavigate, backendOnline }) => {
  const navItems = [
    { id: 'home', label: 'Home', icon: Globe2 },
    { id: 'explorer', label: 'Earth Explorer', icon: Compass },
    { id: 'trend', label: 'Trend Analysis', icon: Activity },
    { id: 'compare', label: 'Compare Regions', icon: GitCompare },
    { id: 'data', label: 'Data Explorer', icon: Database },
    { id: 'about', label: 'About', icon: Info },
  ];

  return (
    <header className="sticky top-0 z-50 glass-panel border-b border-slate-800 bg-navy-950/80 backdrop-blur-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <div 
            onClick={() => onNavigate('home')}
            className="flex items-center gap-3 cursor-pointer group"
          >
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-emerald-600 to-teal-400 flex items-center justify-center shadow-lg shadow-emerald-500/20 group-hover:scale-105 transition-transform">
              <Globe2 className="w-6 h-6 text-navy-950 stroke-[2.5]" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-extrabold text-xl tracking-tight text-white">Earth<span className="text-emerald-400">Trend</span></span>
                <span className="text-[10px] uppercase font-bold tracking-widest px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">NASA 2026</span>
              </div>
              <p className="text-[11px] text-slate-400 font-medium">Earth Intelligence & Environmental Analytics</p>
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="hidden md:flex items-center gap-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = currentPage === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => onNavigate(item.id)}
                  className={`flex items-center gap-2 px-3.5 py-2 rounded-lg text-sm font-medium transition-all ${
                    isActive
                      ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 shadow-sm'
                      : 'text-slate-300 hover:text-white hover:bg-slate-800/60'
                  }`}
                >
                  <Icon className={`w-4 h-4 ${isActive ? 'text-emerald-400' : 'text-slate-400'}`} />
                  {item.label}
                </button>
              );
            })}
          </nav>

          {/* Backend Status indicator */}
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-900/80 border border-slate-800 text-xs">
              <span className={`w-2 h-2 rounded-full ${backendOnline ? 'bg-emerald-400 animate-pulse' : 'bg-amber-400'}`} />
              <span className="text-slate-300 font-mono text-[11px]">
                {backendOnline ? 'NASA API Online' : 'Connecting...'}
              </span>
            </div>
          </div>
        </div>
      </div>
      
      {/* Mobile nav bar */}
      <div className="md:hidden flex overflow-x-auto px-4 py-2 border-t border-slate-800/80 gap-2 bg-slate-950/90">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = currentPage === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onNavigate(item.id)}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium whitespace-nowrap ${
                isActive ? 'bg-emerald-500/20 text-emerald-300' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Icon className="w-3.5 h-3.5" />
              {item.label}
            </button>
          );
        })}
      </div>
    </header>
  );
};
