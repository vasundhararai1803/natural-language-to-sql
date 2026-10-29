import React from 'react';
import type { ContributingFactor } from '../types';
import { TrendingDown, TrendingUp, AlertTriangle } from 'lucide-react';

interface ContributingFactorsProps {
  factors: ContributingFactor[];
}

export const ContributingFactors: React.FC<ContributingFactorsProps> = ({ factors }) => {
  if (!factors || factors.length === 0) return null;

  return (
    <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-5 mb-6 backdrop-blur-sm">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-sm font-semibold text-slate-100 flex items-center gap-2">
            <span>Root-Cause Driver Breakdown</span>
            <span className="text-xs font-normal text-slate-400">
              (Ranked by % share of observed volume change)
            </span>
          </h3>
        </div>
      </div>

      <div className="space-y-3">
        {factors.map((factor, idx) => {
          const isNegative = factor.delta < 0;
          return (
            <div
              key={`${factor.dimension}-${factor.segment}-${idx}`}
              className={`p-3.5 rounded-xl border transition-all ${
                factor.is_anomaly
                  ? 'bg-rose-950/20 border-rose-800/60'
                  : 'bg-slate-800/40 border-slate-700/50 hover:border-slate-600'
              }`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div
                    className={`p-2 rounded-lg ${
                      factor.is_anomaly
                        ? 'bg-rose-500/20 text-rose-400'
                        : isNegative
                        ? 'bg-amber-500/10 text-amber-400'
                        : 'bg-emerald-500/10 text-emerald-400'
                    }`}
                  >
                    {factor.is_anomaly ? (
                      <AlertTriangle className="w-4 h-4" />
                    ) : isNegative ? (
                      <TrendingDown className="w-4 h-4" />
                    ) : (
                      <TrendingUp className="w-4 h-4" />
                    )}
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs uppercase font-mono tracking-wider text-slate-400">
                        {factor.dimension}
                      </span>
                      <span className="text-slate-600">•</span>
                      <span className="text-sm font-medium text-slate-200">{factor.segment}</span>
                      {factor.is_anomaly && (
                        <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded bg-rose-500/30 text-rose-300 border border-rose-500/40">
                          Primary Anomaly
                        </span>
                      )}
                    </div>
                    {factor.note && <p className="text-xs text-slate-400 mt-0.5">{factor.note}</p>}
                  </div>
                </div>

                <div className="text-right">
                  <div className="flex items-center justify-end gap-3">
                    <span className="text-xs text-slate-400">
                      Baseline: {factor.baseline_value.toLocaleString()} → Current:{' '}
                      {factor.current_value.toLocaleString()}
                    </span>
                    <span
                      className={`text-xs font-mono font-bold ${
                        isNegative ? 'text-rose-400' : 'text-emerald-400'
                      }`}
                    >
                      {factor.percentage_change > 0 ? '+' : ''}
                      {factor.percentage_change.toFixed(1)}%
                    </span>
                  </div>
                  {factor.contribution_to_total_drop_pct > 0 && (
                    <div className="text-[11px] text-amber-400/90 font-medium mt-0.5">
                      Contributed {factor.contribution_to_total_drop_pct.toFixed(1)}% to total net decline
                    </div>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
