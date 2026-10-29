import React, { useState } from 'react';
import type { BenchmarkSummary } from '../types';
import {
  CheckCircle2,
  XCircle,
  ShieldCheck,
  Zap,
  Play,
  RotateCcw,
  BarChart2
} from 'lucide-react';

interface EvaluationDashboardProps {
  summary: BenchmarkSummary | null;
  onRunBenchmark: () => void;
  isLoading: boolean;
}

export const EvaluationDashboard: React.FC<EvaluationDashboardProps> = ({
  summary,
  onRunBenchmark,
  isLoading
}) => {
  const [filterDifficulty, setFilterDifficulty] = useState<string>('all');
  const [filterStatus, setFilterStatus] = useState<string>('all');

  if (!summary) {
    return (
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-8 text-center backdrop-blur-sm">
        <BarChart2 className="w-12 h-12 text-sky-400 mx-auto mb-3 opacity-80" />
        <h3 className="text-base font-semibold text-slate-200 mb-1">Empirical Accuracy Benchmark</h3>
        <p className="text-xs text-slate-400 max-w-md mx-auto mb-5">
          Run our 32-case rigorous test suite measuring SQL generation, AST safety checks, intent disambiguation, and edge case guards.
        </p>
        <button
          onClick={onRunBenchmark}
          disabled={isLoading}
          className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-sky-500 hover:bg-sky-400 text-white font-medium text-sm transition-all shadow-lg shadow-sky-500/20 disabled:opacity-50"
        >
          {isLoading ? (
            <RotateCcw className="w-4 h-4 animate-spin" />
          ) : (
            <Play className="w-4 h-4" />
          )}
          Run Full Benchmark
        </button>
      </div>
    );
  }

  const filteredResults = summary.results.filter((r) => {
    if (filterDifficulty !== 'all' && r.difficulty !== filterDifficulty) return false;
    if (filterStatus === 'passed' && !r.passed) return false;
    if (filterStatus === 'failed' && r.passed) return false;
    return true;
  });

  return (
    <div className="space-y-6">
      {/* Top Banner Stats */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 backdrop-blur-sm">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-6 border-b border-slate-800">
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-lg font-bold text-slate-100">Benchmark Evaluation Report</h2>
              <span className="text-xs px-2.5 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                100% Pass Rate Target
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-1">
              Mode: <span className="font-mono text-slate-300">{summary.execution_mode}</span> • Evaluated: {summary.timestamp}
            </p>
          </div>
          <button
            onClick={onRunBenchmark}
            disabled={isLoading}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold border border-slate-700 transition-all disabled:opacity-50"
          >
            <RotateCcw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
            Re-run Benchmark
          </button>
        </div>

        {/* Metric Cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6">
          <div className="p-4 rounded-xl bg-slate-950/40 border border-slate-800/80">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs text-slate-400 font-medium">Overall Accuracy</span>
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            </div>
            <div className="text-2xl font-bold font-mono text-emerald-400">
              {summary.overall_accuracy_pct}%
            </div>
            <p className="text-[11px] text-slate-500 mt-1">
              {summary.passed_tests} / {summary.total_tests} test cases passed
            </p>
          </div>

          <div className="p-4 rounded-xl bg-slate-950/40 border border-slate-800/80">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs text-slate-400 font-medium">SQL Safety Rate</span>
              <ShieldCheck className="w-4 h-4 text-sky-400" />
            </div>
            <div className="text-2xl font-bold font-mono text-sky-400">
              {summary.sql_safety_rate_pct}%
            </div>
            <p className="text-[11px] text-slate-500 mt-1">100% harmful DDL/DML rejected</p>
          </div>

          <div className="p-4 rounded-xl bg-slate-950/40 border border-slate-800/80">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs text-slate-400 font-medium">Execution Accuracy</span>
              <Zap className="w-4 h-4 text-amber-400" />
            </div>
            <div className="text-2xl font-bold font-mono text-amber-400">
              {summary.execution_accuracy_pct}%
            </div>
            <p className="text-[11px] text-slate-500 mt-1">Valid queries executed error-free</p>
          </div>

          <div className="p-4 rounded-xl bg-slate-950/40 border border-slate-800/80">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs text-slate-400 font-medium">Average Latency</span>
              <span className="text-xs font-mono text-slate-500">ms</span>
            </div>
            <div className="text-2xl font-bold font-mono text-slate-200">
              {summary.average_latency_ms} <span className="text-xs font-normal">ms</span>
            </div>
            <p className="text-[11px] text-slate-500 mt-1">Fast deterministic execution</p>
          </div>
        </div>
      </div>

      {/* Test Cases Table with Filters */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 backdrop-blur-sm">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-4">
          <h3 className="text-sm font-semibold text-slate-100">
            Test Case Results ({filteredResults.length})
          </h3>
          <div className="flex items-center gap-2">
            <select
              value={filterDifficulty}
              onChange={(e) => setFilterDifficulty(e.target.value)}
              className="bg-slate-800 border border-slate-700 text-slate-300 text-xs rounded-lg px-2.5 py-1.5 focus:outline-none"
            >
              <option value="all">All Difficulties</option>
              <option value="easy">Easy</option>
              <option value="medium">Medium</option>
              <option value="hard">Hard</option>
              <option value="safety">Safety</option>
              <option value="edge_case">Edge Case</option>
            </select>

            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="bg-slate-800 border border-slate-700 text-slate-300 text-xs rounded-lg px-2.5 py-1.5 focus:outline-none"
            >
              <option value="all">All Outcomes</option>
              <option value="passed">Passed</option>
              <option value="failed">Failed</option>
            </select>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950/60 text-slate-400 uppercase font-mono text-[10px] border-b border-slate-800">
              <tr>
                <th className="py-2.5 px-3">ID</th>
                <th className="py-2.5 px-3">Question</th>
                <th className="py-2.5 px-3">Category</th>
                <th className="py-2.5 px-3">Difficulty</th>
                <th className="py-2.5 px-3">Status</th>
                <th className="py-2.5 px-3">Latency</th>
                <th className="py-2.5 px-3">Result</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {filteredResults.map((r) => (
                <tr key={r.test_id} className="hover:bg-slate-800/20 transition-colors">
                  <td className="py-2.5 px-3 font-mono font-semibold text-sky-400">{r.test_id}</td>
                  <td className="py-2.5 px-3 text-slate-200 max-w-sm truncate" title={r.question}>
                    {r.question}
                  </td>
                  <td className="py-2.5 px-3 font-mono text-[11px] text-slate-400">{r.category}</td>
                  <td className="py-2.5 px-3">
                    <span
                      className={`text-[10px] font-mono px-2 py-0.5 rounded ${
                        r.difficulty === 'safety'
                          ? 'bg-rose-950/50 text-rose-300 border border-rose-800/50'
                          : r.difficulty === 'hard'
                          ? 'bg-purple-950/50 text-purple-300 border border-purple-800/50'
                          : 'bg-slate-800 text-slate-300'
                      }`}
                    >
                      {r.difficulty}
                    </span>
                  </td>
                  <td className="py-2.5 px-3 font-mono text-[11px] text-slate-300">
                    {r.execution_status}
                  </td>
                  <td className="py-2.5 px-3 font-mono text-slate-400">{r.latency_ms}ms</td>
                  <td className="py-2.5 px-3">
                    {r.passed ? (
                      <span className="inline-flex items-center gap-1 text-emerald-400 font-semibold">
                        <CheckCircle2 className="w-3.5 h-3.5" /> Passed
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 text-rose-400 font-semibold">
                        <XCircle className="w-3.5 h-3.5" /> Failed
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
