import React, { useState } from 'react';
import { Copy, Check, Download, Table, Code2, AlertTriangle, Info, Sparkles } from 'lucide-react';
import type { QueryResponse } from '../types';
import { DynamicChart } from './DynamicChart';
import { ContributingFactors } from './ContributingFactors';

interface AnalysisResultProps {
  response: QueryResponse;
  onSelectFollowUp: (q: string) => void;
}

export const AnalysisResult: React.FC<AnalysisResultProps> = ({ response, onSelectFollowUp }) => {
  const [activeTab, setActiveTab] = useState<'chart' | 'table' | 'sql'>('chart');
  const [copied, setCopied] = useState(false);

  const handleCopySQL = () => {
    if (response.sql) {
      navigator.clipboard.writeText(response.sql);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleExportCSV = () => {
    if (!response.rows || response.rows.length === 0) return;
    const headers = response.columns.join(',');
    const csvRows = response.rows.map((row) =>
      response.columns.map((col) => JSON.stringify(row[col] ?? '')).join(',')
    );
    const csvContent = 'data:text/csv;charset=utf-8,' + [headers, ...csvRows].join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `querylens_${response.request_id}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="space-y-6">
      {/* Executive Summary Card */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 backdrop-blur-sm relative overflow-hidden">
        <div className="flex items-start justify-between gap-4 mb-3">
          <div className="flex items-center gap-2">
            <span className="p-1.5 rounded-lg bg-sky-500/10 text-sky-400">
              <Sparkles className="w-4 h-4" />
            </span>
            <span className="text-xs uppercase font-mono tracking-wider text-slate-400">
              Executive Finding
            </span>
          </div>
          <div className="flex items-center gap-2">
            <span
              className={`text-xs px-2.5 py-0.5 rounded-full font-mono border ${
                response.query_status === 'success'
                  ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                  : response.query_status === 'clarification'
                  ? 'bg-amber-500/10 text-amber-400 border-amber-500/30'
                  : 'bg-rose-500/10 text-rose-400 border-rose-500/30'
              }`}
            >
              {response.query_status.toUpperCase()}
            </span>
            <span className="text-xs text-slate-500 font-mono">
              {response.execution_time_ms}ms
            </span>
          </div>
        </div>

        <h3 className="text-base md:text-lg font-medium text-slate-100 leading-relaxed mb-4">
          {response.summary}
        </h3>

        {/* Metric Cards if diagnostic */}
        {response.metric_cards && response.metric_cards.length > 0 && (
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-4">
            {response.metric_cards.map((card, idx) => (
              <div
                key={idx}
                className="bg-slate-950/40 border border-slate-800/80 rounded-xl p-3.5"
              >
                <div className="text-xs text-slate-400">{card.label}</div>
                <div className="text-xl font-bold font-mono text-slate-100 mt-1">
                  {card.value}
                </div>
                {card.change_pct !== undefined && card.change_pct !== null && (
                  <div
                    className={`text-xs font-mono font-medium mt-1 ${
                      card.sentiment === 'negative'
                        ? 'text-rose-400'
                        : card.sentiment === 'positive'
                        ? 'text-emerald-400'
                        : 'text-slate-400'
                    }`}
                  >
                    {card.change_pct > 0 ? '+' : ''}
                    {card.change_pct}% {card.comparison_label}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        {/* Grounded Key Findings */}
        {response.key_findings && response.key_findings.length > 0 && (
          <div className="space-y-1.5 pt-2 border-t border-slate-800/80">
            {response.key_findings.map((f, idx) => (
              <div key={idx} className="flex items-start gap-2 text-xs text-slate-300">
                <span className="text-sky-400 font-bold mt-0.5">•</span>
                <span>{f}</span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Contributing Factors Breakdown (if diagnostic 'Why did this change?') */}
      {response.contributing_factors && response.contributing_factors.length > 0 && (
        <ContributingFactors factors={response.contributing_factors} />
      )}

      {/* Visualization & Table Section */}
      {response.rows && response.rows.length > 0 && (
        <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 backdrop-blur-sm">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-4">
            <div className="flex bg-slate-800/80 p-1 rounded-xl border border-slate-700/60">
              {response.chart_spec && (
                <button
                  onClick={() => setActiveTab('chart')}
                  className={`px-3 py-1.5 text-xs font-medium rounded-lg transition-all ${
                    activeTab === 'chart'
                      ? 'bg-sky-500 text-white shadow'
                      : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  Chart View
                </button>
              )}
              <button
                onClick={() => setActiveTab('table')}
                className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg transition-all ${
                  activeTab === 'table'
                    ? 'bg-sky-500 text-white shadow'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                <Table className="w-3.5 h-3.5" /> Table ({response.row_count})
              </button>
              <button
                onClick={() => setActiveTab('sql')}
                className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg transition-all ${
                  activeTab === 'sql'
                    ? 'bg-sky-500 text-white shadow'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                <Code2 className="w-3.5 h-3.5" /> Generated SQL
              </button>
            </div>

            <button
              onClick={handleExportCSV}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-700 text-xs text-slate-300 font-medium transition-colors"
            >
              <Download className="w-3.5 h-3.5" /> Export CSV
            </button>
          </div>

          {activeTab === 'chart' && response.chart_spec && (
            <DynamicChart spec={response.chart_spec} data={response.rows} />
          )}

          {activeTab === 'table' && (
            <div className="overflow-x-auto rounded-xl border border-slate-800 bg-slate-950/40">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-900 text-slate-400 uppercase font-mono text-[10px] border-b border-slate-800">
                  <tr>
                    {response.columns.map((c) => (
                      <th key={c} className="py-2.5 px-3 font-semibold">
                        {c}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 font-mono">
                  {response.rows.map((row, rIdx) => (
                    <tr key={rIdx} className="hover:bg-slate-800/20 transition-colors">
                      {response.columns.map((col) => (
                        <td key={col} className="py-2 px-3 text-slate-300 whitespace-nowrap">
                          {row[col] !== null && row[col] !== undefined
                            ? String(row[col])
                            : <span className="text-slate-600 italic">null</span>}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {activeTab === 'sql' && (
            <div className="relative">
              <pre className="p-4 rounded-xl bg-slate-950 border border-slate-800 font-mono text-xs text-sky-300 overflow-x-auto leading-relaxed">
                {response.sql}
              </pre>
              <button
                onClick={handleCopySQL}
                className="absolute top-3 right-3 p-1.5 rounded-lg bg-slate-800/80 hover:bg-slate-700 text-slate-300 border border-slate-700"
                title="Copy SQL"
              >
                {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
              </button>
            </div>
          )}
        </div>
      )}

      {/* Assumptions, Confidence & Limitations Notice */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="p-4 rounded-xl bg-slate-900/40 border border-slate-800/60 text-xs text-slate-400">
          <div className="flex items-center gap-1.5 text-slate-300 font-medium mb-1.5">
            <Info className="w-3.5 h-3.5 text-sky-400" />
            <span>Assumptions & Interpretation</span>
          </div>
          {response.assumptions && response.assumptions.length > 0 ? (
            <ul className="list-disc list-inside space-y-1 text-slate-400">
              {response.assumptions.map((a, i) => (
                <li key={i}>{a}</li>
              ))}
            </ul>
          ) : (
            <p>Direct relational aggregation without unstated approximations.</p>
          )}
        </div>

        <div className="p-4 rounded-xl bg-slate-900/40 border border-slate-800/60 text-xs text-slate-400">
          <div className="flex items-center gap-1.5 text-amber-400 font-medium mb-1.5">
            <AlertTriangle className="w-3.5 h-3.5" />
            <span>Data Boundaries & Causality</span>
          </div>
          <ul className="list-disc list-inside space-y-1 text-slate-400">
            {response.limitations && response.limitations.length > 0 ? (
              response.limitations.map((l, i) => <li key={i}>{l}</li>)
            ) : (
              <li>Correlation in purchase records does not imply direct causality.</li>
            )}
          </ul>
        </div>
      </div>

      {/* Follow-up suggestions */}
      {response.follow_up_questions && response.follow_up_questions.length > 0 && (
        <div className="pt-2">
          <span className="text-xs font-medium text-slate-400 block mb-2">
            Suggested Next Inquiries:
          </span>
          <div className="flex flex-wrap gap-2">
            {response.follow_up_questions.map((q, idx) => (
              <button
                key={idx}
                onClick={() => onSelectFollowUp(q)}
                className="text-xs px-3 py-1.5 rounded-xl bg-slate-800/80 hover:bg-slate-800 text-slate-300 hover:text-sky-300 border border-slate-700/60 transition-all text-left"
              >
                ➔ {q}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
