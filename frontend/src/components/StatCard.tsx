import React from 'react';
import type { LucideIcon } from 'lucide-react';


interface StatCardProps {
  title: string;
  value: string | number;
  icon: LucideIcon;
  color: 'blue' | 'green' | 'purple' | 'amber' | 'cyan';
  subtitle?: string;
}

export const StatCard: React.FC<StatCardProps> = ({ title, value, icon: Icon, color, subtitle }) => {
  const colorMap = {
    blue: 'from-blue-500/20 to-blue-600/5 text-blue-400 border-blue-500/30',
    green: 'from-emerald-500/20 to-emerald-600/5 text-emerald-400 border-emerald-500/30',
    purple: 'from-purple-500/20 to-purple-600/5 text-purple-400 border-purple-500/30',
    amber: 'from-amber-500/20 to-amber-600/5 text-amber-400 border-amber-500/30',
    cyan: 'from-cyan-500/20 to-cyan-600/5 text-cyan-400 border-cyan-500/30',
  };

  const iconBgMap = {
    blue: 'bg-blue-500/10 text-blue-400',
    green: 'bg-emerald-500/10 text-emerald-400',
    purple: 'bg-purple-500/10 text-purple-400',
    amber: 'bg-amber-500/10 text-amber-400',
    cyan: 'bg-cyan-500/10 text-cyan-400',
  };

  return (
    <div className={`p-6 rounded-2xl bg-gradient-to-b ${colorMap[color]} border backdrop-blur-md transition-all duration-300 hover:scale-[1.02] hover:shadow-xl shadow-black/20`}>
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs font-semibold tracking-wider text-slate-400 uppercase">{title}</p>
          <h3 className="text-3xl font-extrabold text-white mt-1">{value}</h3>
          {subtitle && <p className="text-xs text-slate-400 mt-1">{subtitle}</p>}
        </div>
        <div className={`p-3.5 rounded-xl ${iconBgMap[color]}`}>
          <Icon className="w-7 h-7" />
        </div>
      </div>
    </div>
  );
};
