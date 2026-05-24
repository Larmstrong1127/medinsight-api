import { useState } from "react";
import Header from "./components/Header";
import AnalyzePanel from "./components/AnalyzePanel";
import ResultsPanel from "./components/ResultsPanel";
import AgentPanel from "./components/AgentPanel";
import AuditLog from "./components/AuditLog";
import "./index.css";

const TABS = ["Analyze", "Agent"];

export default function App() {
  const [tab, setTab] = useState("Analyze");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [auditRefresh, setAuditRefresh] = useState(0);

  const handleResult = (r) => {
    setResult(r);
    setAuditRefresh((v) => v + 1);
  };

  return (
    <div className="min-h-screen bg-navy-900 flex flex-col">
      <Header />

      <main className="flex-1 max-w-7xl mx-auto w-full px-6 py-8 flex flex-col gap-6">
        {/* Tab bar */}
        <div className="flex gap-1 bg-navy-800 border border-slate-700/50 rounded-lg p-1 w-fit">
          {TABS.map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`px-4 py-1.5 rounded-md text-sm font-medium transition-colors ${
                tab === t
                  ? "bg-navy-600 text-white"
                  : "text-slate-400 hover:text-slate-300"
              }`}
            >
              {t}
            </button>
          ))}
        </div>

        {tab === "Analyze" && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <AnalyzePanel onResult={handleResult} onLoading={setLoading} />
            <ResultsPanel result={result} loading={loading} />
          </div>
        )}

        {tab === "Agent" && <AgentPanel />}

        <AuditLog refreshTrigger={auditRefresh} />
      </main>
    </div>
  );
}
