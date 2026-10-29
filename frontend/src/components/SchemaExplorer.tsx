import React, { useState } from 'react';
import type { SchemaTable, MetricDefinition } from '../types';
import { Database, Table, Key, ChevronRight, ChevronDown } from 'lucide-react';

interface SchemaExplorerProps {
  tables: SchemaTable[];
  metrics: MetricDefinition[];
}

export const SchemaExplorer: React.FC<SchemaExplorerProps> = ({ tables, metrics }) => {
  const [expandedTable, setExpandedTable] = useState<string | null>(tables[0]?.table_name || null);
  const [activeTab, setActiveTab] = useState<'tables' | 'metrics'>('tables');

  return (
    <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 backdrop-blur-sm">
      <div className="flex items-center justify-between pb-4 border-b border-slate-800 mb-5">
        <div className="flex items-center gap-2.5">
          <Database className="w-5 h-5 text-sky-400" />
          <h2 className="text-base font-semibold text-slate-100">Database & Metric Catalog</h2>
        </div>
        <div className="flex bg-slate-800/80 p-1 rounded-xl border border-slate-700/60">
          <button
            onClick={() => setActiveTab('tables')}
            className={`px-3 py-1 text-xs font-medium rounded-lg transition-all ${
              activeTab === 'tables' ? 'bg-sky-500 text-white shadow' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Tables ({tables.length})
          </button>
          <button
            onClick={() => setActiveTab('metrics')}
            className={`px-3 py-1 text-xs font-medium rounded-lg transition-all ${
              activeTab === 'metrics' ? 'bg-sky-500 text-white shadow' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Metrics ({metrics.length})
          </button>
        </div>
      </div>

      {activeTab === 'tables' ? (
        <div className="space-y-3">
          {tables.map((tbl) => {
            const isExpanded = expandedTable === tbl.table_name;
            return (
              <div
                key={tbl.table_name}
                className="border border-slate-800/90 rounded-xl overflow-hidden bg-slate-900/40 transition-colors"
              >
                <button
                  onClick={() => setExpandedTable(isExpanded ? null : tbl.table_name)}
                  className="w-full flex items-center justify-between p-3.5 text-left hover:bg-slate-800/30 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <Table className="w-4 h-4 text-sky-400" />
                    <div>
                      <span className="font-mono text-sm font-semibold text-slate-100">{tbl.table_name}</span>
                      <p className="text-xs text-slate-400 mt-0.5">{tbl.description}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-slate-400 font-mono">{tbl.columns.length} cols</span>
                    {isExpanded ? (
                      <ChevronDown className="w-4 h-4 text-slate-500" />
                    ) : (
                      <ChevronRight className="w-4 h-4 text-slate-500" />
                    )}
                  </div>
                </button>

                {isExpanded && (
                  <div className="border-t border-slate-800/80 p-4 bg-slate-950/40">
                    <div className="grid grid-cols-1 gap-2">
                      {tbl.columns.map((col) => (
                        <div
                          key={col.name}
                          className="flex items-center justify-between py-1.5 px-3 rounded-lg bg-slate-900/60 border border-slate-800/50 text-xs"
                        >
                          <div className="flex items-center gap-2">
                            {col.primary_key ? (
                              <Key className="w-3.5 h-3.5 text-amber-400" />
                            ) : (
                              <div className="w-3.5 h-3.5" />
                            )}
                            <span className="font-mono font-medium text-slate-200">{col.name}</span>
                            <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-800 text-slate-400">
                              {col.type}
                            </span>
                            {col.foreign_key && (
                              <span className="text-[10px] text-sky-400 font-mono">
                                ➔ {col.foreign_key}
                              </span>
                            )}
                          </div>
                          <span className="text-slate-400 text-[11px] truncate max-w-xs">{col.description}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {metrics.map((m) => (
            <div
              key={m.metric_id}
              className="p-4 rounded-xl border border-slate-800/80 bg-slate-900/40 flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <h4 className="text-sm font-semibold text-slate-200">{m.name}</h4>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-sky-950/40 text-sky-400 border border-sky-800/50">
                    {m.metric_id}
                  </span>
                </div>
                <p className="text-xs text-slate-400 mb-3">{m.business_meaning}</p>
              </div>
              <div className="bg-slate-950/60 p-2.5 rounded-lg border border-slate-800 font-mono text-[11px] text-emerald-400 overflow-x-auto">
                {m.formula}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
