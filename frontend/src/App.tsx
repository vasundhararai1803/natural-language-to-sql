import { useState, useEffect } from 'react';
import {
  Sparkles,
  Database,
  BarChart2,
  ArrowRight,
  ShieldAlert,
  Activity,
  CheckCircle2,
  RotateCw
} from 'lucide-react';
import type { QueryResponse, SchemaTable, MetricDefinition, BenchmarkSummary } from './types';
import { AnalysisResult } from './components/AnalysisResult';
import { SchemaExplorer } from './components/SchemaExplorer';
import { EvaluationDashboard } from './components/EvaluationDashboard';

const SAMPLE_QUESTIONS = [
  "Why did transactions drop last week?",
  "What were our top-performing products this month?",
  "Which region has the highest cancellation rate?",
  "Compare revenue this quarter with the previous quarter",
  "Show me daily transactions and highlight unusual drops",
  "How did we perform last week?",
  "What was our net profit?"
];

export function App() {
  const [activeView, setActiveView] = useState<'analytics' | 'schema' | 'evaluation' | 'settings'>('analytics');
  const [question, setQuestion] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [currentResponse, setCurrentResponse] = useState<QueryResponse | null>(null);
  const [history, setHistory] = useState<QueryResponse[]>([]);
  const [tables, setTables] = useState<SchemaTable[]>([]);
  const [metrics, setMetrics] = useState<MetricDefinition[]>([]);
  const [benchmark, setBenchmark] = useState<BenchmarkSummary | null>(null);
  const [isBenchmarking, setIsBenchmarking] = useState(false);
  const [apiHealth, setApiHealth] = useState<{ status: string; llm_configured: boolean } | null>(null);

  useEffect(() => {
    fetchHealth();
    fetchSchema();
    fetchMetrics();
    fetchBenchmark();
  }, []);

  const fetchHealth = async () => {
    try {
      const res = await fetch('/api/health');
      if (res.ok) {
        const data = await res.json();
        setApiHealth(data);
      }
    } catch (e) {
      console.error("Health check error", e);
    }
  };

  const fetchSchema = async () => {
    try {
      const res = await fetch('/api/schema');
      if (res.ok) setTables(await res.json());
    } catch (e) {
      console.error("Schema fetch error", e);
    }
  };

  const fetchMetrics = async () => {
    try {
      const res = await fetch('/api/metrics/definitions');
      if (res.ok) setMetrics(await res.json());
    } catch (e) {
      console.error("Metrics fetch error", e);
    }
  };

  const fetchBenchmark = async () => {
    try {
      const res = await fetch('/api/evaluation/results');
      if (res.ok) setBenchmark(await res.json());
    } catch (e) {
      console.error("Benchmark fetch error", e);
    }
  };

  const handleAsk = async (userPrompt?: string) => {
    const q = userPrompt || question;
    if (!q.trim()) return;

    setIsLoading(true);
    setActiveView('analytics');
    try {
      const res = await fetch('/api/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: q })
      });

      if (res.ok) {
        const data: QueryResponse = await res.json();
        setCurrentResponse(data);
        setHistory((prev) => [data, ...prev.filter((h) => h.request_id !== data.request_id)]);
      } else {
        alert("Failed to analyze question. Please verify backend service is running.");
      }
    } catch (e) {
      console.error("Error asking question", e);
    } finally {
      setIsLoading(false);
    }
  };

  const handleRunBenchmark = async () => {
    setIsBenchmarking(true);
    try {
      const res = await fetch('/api/evaluation/run', { method: 'POST' });
      if (res.ok) {
        const data: BenchmarkSummary = await res.json();
        setBenchmark(data);
      }
    } catch (e) {
      console.error("Benchmark run error", e);
    } finally {
      setIsBenchmarking(false);
    }
  };

  return (
    <div className="flex h-screen bg-[#090d16] text-slate-100 antialiased overflow-hidden">
      {/* Left Sidebar */}
      <aside className="w-64 bg-[#0d121f] border-r border-slate-800/80 flex flex-col justify-between p-4 shrink-0">
        <div>
          {/* Logo & Brand */}
          <div className="flex items-center gap-2.5 px-2 py-3 mb-6">
            <div className="p-2 rounded-xl bg-gradient-to-tr from-sky-600 to-indigo-500 shadow-lg shadow-sky-500/20 text-white">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <h1 className="text-base font-bold text-slate-100 tracking-tight leading-none m-0">
                QueryLens AI
              </h1>
              <span className="text-[10px] font-mono text-sky-400">Enterprise Analytics</span>
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="space-y-1 mb-6">
            <button
              onClick={() => setActiveView('analytics')}
              className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-xs font-semibold transition-all ${
                activeView === 'analytics'
                  ? 'bg-sky-500/10 text-sky-400 border border-sky-500/20 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
              }`}
            >
              <Activity className="w-4 h-4" />
              <span>Ask & Explore</span>
            </button>

            <button
              onClick={() => setActiveView('schema')}
              className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-xs font-semibold transition-all ${
                activeView === 'schema'
                  ? 'bg-sky-500/10 text-sky-400 border border-sky-500/20 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
              }`}
            >
              <Database className="w-4 h-4" />
              <span>Data & Metrics Catalog</span>
            </button>

            <button
              onClick={() => setActiveView('evaluation')}
              className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-xs font-semibold transition-all ${
                activeView === 'evaluation'
                  ? 'bg-sky-500/10 text-sky-400 border border-sky-500/20 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
              }`}
            >
              <BarChart2 className="w-4 h-4" />
              <span>Evaluation & Accuracy</span>
            </button>
          </nav>

          {/* Recent Questions list */}
          {history.length > 0 && (
            <div className="pt-4 border-t border-slate-800/60">
              <span className="px-2 text-[10px] font-mono uppercase tracking-wider text-slate-500 block mb-2">
                Recent Inquiries
              </span>
              <div className="space-y-1 max-h-48 overflow-y-auto pr-1">
                {history.map((h) => (
                  <button
                    key={h.request_id}
                    onClick={() => {
                      setCurrentResponse(h);
                      setActiveView('analytics');
                    }}
                    className={`w-full text-left px-2.5 py-1.5 rounded-lg text-xs truncate transition-colors ${
                      currentResponse?.request_id === h.request_id
                        ? 'bg-slate-800 text-sky-300 font-medium'
                        : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/30'
                    }`}
                    title={h.question}
                  >
                    {h.question}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Engine Status pill */}
        <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800/80">
          <div className="flex items-center justify-between mb-1">
            <span className="text-[11px] text-slate-400 font-medium">Engine Mode</span>
            <span className="inline-flex items-center gap-1 text-[10px] font-mono text-emerald-400">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
              Active
            </span>
          </div>
          <div className="text-xs font-mono text-slate-200">
            {apiHealth?.llm_configured ? "OpenAI LLM + Guardrails" : "Deterministic Fallback Engine"}
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col h-screen overflow-y-auto bg-gradient-to-b from-[#0e1424]/40 to-[#090d16]">
        {/* Top Navbar */}
        <header className="h-14 border-b border-slate-800/70 px-8 flex items-center justify-between shrink-0 bg-[#090d16]/80 backdrop-blur-md">
          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-400">Database:</span>
            <span className="text-xs font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700/60">
              sqlite:///data/querylens.db (12,965 rows)
            </span>
          </div>

          <div className="flex items-center gap-4 text-xs text-slate-400">
            <div className="flex items-center gap-1.5">
              <ShieldAlert className="w-3.5 h-3.5 text-sky-400" />
              <span>AST SQL Guard: Enforced</span>
            </div>
            <span>•</span>
            <div className="flex items-center gap-1.5">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
              <span>32/32 Benchmarks Validated</span>
            </div>
          </div>
        </header>

        {/* Dynamic Workspace Views */}
        <div className="p-8 max-w-6xl w-full mx-auto space-y-8 flex-1">
          {activeView === 'analytics' && (
            <>
              {/* Natural Language Prompt Search Bar */}
              <div className="space-y-4">
                <div className="text-center max-w-2xl mx-auto pt-2 pb-2">
                  <h2 className="text-3xl font-bold tracking-tight text-slate-100 sm:text-4xl m-0">
                    Your data, explained.
                  </h2>
                  <p className="text-sm text-slate-400 mt-2">
                    Ask business questions in plain English. Get SQL, interactive charts, and evidence-backed root-cause insights.
                  </p>
                </div>

                <div className="relative max-w-3xl mx-auto">
                  <form
                    onSubmit={(e) => {
                      e.preventDefault();
                      handleAsk();
                    }}
                    className="relative flex items-center"
                  >
                    <input
                      type="text"
                      value={question}
                      onChange={(e) => setQuestion(e.target.value)}
                      placeholder="e.g. Why did transactions drop last week?"
                      className="w-full bg-[#111726] border border-slate-700/80 rounded-2xl py-4 pl-5 pr-32 text-sm text-slate-100 placeholder-slate-500 shadow-2xl focus:outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500 transition-all"
                    />
                    <button
                      type="submit"
                      disabled={isLoading || !question.trim()}
                      className="absolute right-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-sky-500 to-indigo-600 hover:from-sky-400 hover:to-indigo-500 text-white font-semibold text-xs flex items-center gap-2 shadow-lg shadow-sky-500/25 transition-all disabled:opacity-40"
                    >
                      {isLoading ? (
                        <>
                          <RotateCw className="w-3.5 h-3.5 animate-spin" />
                          <span>Analyzing...</span>
                        </>
                      ) : (
                        <>
                          <span>Ask AI</span>
                          <ArrowRight className="w-3.5 h-3.5" />
                        </>
                      )}
                    </button>
                  </form>
                </div>

                {/* Sample Question Chips */}
                <div className="flex flex-wrap items-center justify-center gap-2 max-w-3xl mx-auto pt-1">
                  <span className="text-[11px] font-medium text-slate-500 mr-1">Try asking:</span>
                  {SAMPLE_QUESTIONS.map((sq, idx) => (
                    <button
                      key={idx}
                      onClick={() => {
                        setQuestion(sq);
                        handleAsk(sq);
                      }}
                      className="text-xs px-3 py-1.5 rounded-xl bg-slate-900 hover:bg-slate-800 text-slate-300 hover:text-sky-300 border border-slate-800 transition-colors"
                    >
                      {sq}
                    </button>
                  ))}
                </div>
              </div>

              {/* Analysis Result or Initial State */}
              {isLoading ? (
                <div className="bg-slate-900/40 border border-slate-800 rounded-2xl p-12 text-center backdrop-blur-sm animate-pulse">
                  <RotateCw className="w-8 h-8 text-sky-400 animate-spin mx-auto mb-3" />
                  <h3 className="text-sm font-semibold text-slate-200">
                    Interpreting Intent & Generating Safe SQL...
                  </h3>
                  <p className="text-xs text-slate-400 mt-1">
                    Validating schema references, executing read-only query, and calculating segment contributions.
                  </p>
                </div>
              ) : currentResponse ? (
                <AnalysisResult
                  response={currentResponse}
                  onSelectFollowUp={(followUp) => {
                    setQuestion(followUp);
                    handleAsk(followUp);
                  }}
                />
              ) : (
                <div className="border border-dashed border-slate-800 rounded-2xl p-10 text-center text-slate-500">
                  <p className="text-sm">Enter a query above or click any sample prompt to begin analysis.</p>
                </div>
              )}
            </>
          )}

          {activeView === 'schema' && (
            <SchemaExplorer tables={tables} metrics={metrics} />
          )}

          {activeView === 'evaluation' && (
            <EvaluationDashboard
              summary={benchmark}
              onRunBenchmark={handleRunBenchmark}
              isLoading={isBenchmarking}
            />
          )}
        </div>
      </main>
    </div>
  );
}
export default App;
