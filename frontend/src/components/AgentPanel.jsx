import { useState } from "react";
import { agentQuery } from "../api/client";

export default function AgentPanel() {
  const [query, setQuery] = useState("");
  const [patientId, setPatientId] = useState("");
  const [loading, setLoading] = useState(false);
  const [answer, setAnswer] = useState(null);
  const [error, setError] = useState(null);

  const handleQuery = async () => {
    if (!query.trim()) return;
    setLoading(true);
    setError(null);
    setAnswer(null);
    try {
      const res = await agentQuery(query, patientId || null);
      setAnswer(res.data.answer);
    } catch (err) {
      setError(err.response?.data?.detail || "Agent query failed.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-navy-800 border border-slate-700/50 rounded-xl p-6 flex flex-col gap-4">
      <div className="flex items-center gap-2">
        <div className="w-6 h-6 rounded bg-purple-500/20 border border-purple-500/40 flex items-center justify-center">
          <span className="text-purple-400 text-xs">✦</span>
        </div>
        <h2 className="text-white font-semibold text-base">Clinical Agent</h2>
        <span className="text-xs text-purple-400 bg-purple-500/10 border border-purple-500/20 px-2 py-0.5 rounded-full">
          LangChain
        </span>
      </div>

      <p className="text-slate-500 text-xs">
        Ask freeform questions. The agent will search documents, summarize, and assess risks automatically.
      </p>

      <div className="grid grid-cols-3 gap-3">
        <div className="col-span-2">
          <label className="text-xs text-slate-500 mb-1 block">Query</label>
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleQuery()}
            placeholder="What are the risk factors for this patient?"
            className="w-full bg-navy-900 border border-slate-700/50 rounded-lg px-3 py-2 text-sm text-slate-300 placeholder-slate-600 focus:outline-none focus:border-purple-500/50"
          />
        </div>
        <div>
          <label className="text-xs text-slate-500 mb-1 block">Patient ID (optional)</label>
          <input
            value={patientId}
            onChange={(e) => setPatientId(e.target.value)}
            placeholder="pt-synthetic-001"
            className="w-full bg-navy-900 border border-slate-700/50 rounded-lg px-3 py-2 text-sm text-slate-300 placeholder-slate-600 focus:outline-none focus:border-purple-500/50"
          />
        </div>
      </div>

      <div className="flex gap-2 flex-wrap">
        {[
          "Summarize documents for pt-synthetic-001",
          "What diagnoses appear across all documents?",
          "List risk factors for pt-synthetic-004",
        ].map((s) => (
          <button
            key={s}
            onClick={() => setQuery(s)}
            className="text-xs text-slate-400 bg-navy-900 border border-slate-700/50 px-2.5 py-1 rounded-lg hover:text-slate-300 transition-colors"
          >
            {s}
          </button>
        ))}
      </div>

      {error && (
        <p className="text-red-400 text-xs bg-red-500/10 border border-red-500/20 rounded-lg px-3 py-2">{error}</p>
      )}

      {loading && (
        <div className="flex items-center gap-2 text-slate-500 text-sm">
          <div className="w-4 h-4 border-2 border-purple-500/30 border-t-purple-500 rounded-full animate-spin" />
          Agent is thinking...
        </div>
      )}

      {answer && (
        <div className="bg-navy-900 border border-purple-500/20 rounded-lg p-4">
          <p className="text-xs text-purple-400 mb-2 font-medium">Agent Response</p>
          <p className="text-slate-300 text-sm leading-relaxed whitespace-pre-wrap">{answer}</p>
        </div>
      )}

      <button
        onClick={handleQuery}
        disabled={loading || !query.trim()}
        className="w-full py-2.5 rounded-lg bg-purple-600 hover:bg-purple-500 disabled:bg-slate-700 disabled:text-slate-500 text-white text-sm font-medium transition-colors"
      >
        {loading ? "Querying..." : "Ask Agent"}
      </button>
    </div>
  );
}
