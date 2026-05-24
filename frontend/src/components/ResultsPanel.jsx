const SEVERITY_COLORS = {
  low: "text-emerald-400 bg-emerald-500/10 border-emerald-500/20",
  medium: "text-yellow-400 bg-yellow-500/10 border-yellow-500/20",
  high: "text-red-400 bg-red-500/10 border-red-500/20",
};

function Section({ title, children, count }) {
  return (
    <div className="border border-slate-700/50 rounded-lg overflow-hidden">
      <div className="bg-navy-700/50 px-4 py-2.5 flex items-center justify-between">
        <span className="text-slate-300 text-sm font-medium">{title}</span>
        {count !== undefined && (
          <span className="text-xs text-slate-500 bg-navy-900 px-2 py-0.5 rounded-full">{count}</span>
        )}
      </div>
      <div className="p-4">{children}</div>
    </div>
  );
}

export default function ResultsPanel({ result, loading }) {
  if (loading) {
    return (
      <div className="bg-navy-800 border border-slate-700/50 rounded-xl p-6 flex flex-col items-center justify-center min-h-[400px] gap-3">
        <div className="w-8 h-8 border-2 border-blue-500/30 border-t-blue-500 rounded-full animate-spin" />
        <p className="text-slate-500 text-sm">Analyzing with GPT-4o-mini...</p>
      </div>
    );
  }

  if (!result) {
    return (
      <div className="bg-navy-800 border border-slate-700/50 rounded-xl p-6 flex flex-col items-center justify-center min-h-[400px] gap-2">
        <div className="w-12 h-12 rounded-xl bg-navy-700 flex items-center justify-center text-2xl mb-2">🔬</div>
        <p className="text-slate-400 text-sm font-medium">No analysis yet</p>
        <p className="text-slate-600 text-xs text-center">Paste a clinical note and click Analyze</p>
      </div>
    );
  }

  const { result: r, analysis_type, model_used, created_at } = result;

  return (
    <div className="bg-navy-800 border border-slate-700/50 rounded-xl p-6 flex flex-col gap-4 overflow-y-auto">
      <div className="flex items-center justify-between">
        <h2 className="text-white font-semibold text-base">Analysis Results</h2>
        <div className="flex items-center gap-2 text-xs text-slate-500">
          <span className="bg-navy-900 px-2 py-1 rounded border border-slate-700/50">{model_used}</span>
          <span>{new Date(created_at).toLocaleTimeString()}</span>
        </div>
      </div>

      {r.summary && (
        <Section title="Summary">
          <p className="text-slate-300 text-sm leading-relaxed">{r.summary}</p>
        </Section>
      )}

      {r.diagnoses?.length > 0 && (
        <Section title="Diagnoses" count={r.diagnoses.length}>
          <div className="flex flex-col gap-2">
            {r.diagnoses.map((d, i) => (
              <div key={i} className="flex items-start justify-between gap-3">
                <div className="flex items-center gap-2">
                  {d.code && (
                    <span className="text-xs font-mono bg-navy-900 text-blue-400 px-1.5 py-0.5 rounded border border-slate-700/50 whitespace-nowrap">
                      {d.code}
                    </span>
                  )}
                  <span className="text-slate-300 text-sm">{d.description}</span>
                </div>
                <span className="text-xs text-slate-500 whitespace-nowrap">
                  {Math.round(d.confidence * 100)}%
                </span>
              </div>
            ))}
          </div>
        </Section>
      )}

      {r.medications?.length > 0 && (
        <Section title="Medications" count={r.medications.length}>
          <div className="flex flex-wrap gap-2">
            {r.medications.map((m, i) => (
              <div key={i} className="bg-navy-900 border border-slate-700/50 rounded-lg px-3 py-2 text-sm">
                <span className="text-slate-200 font-medium">{m.name}</span>
                {(m.dosage || m.frequency) && (
                  <span className="text-slate-500 ml-1.5 text-xs">
                    {[m.dosage, m.frequency, m.route].filter(Boolean).join(" · ")}
                  </span>
                )}
              </div>
            ))}
          </div>
        </Section>
      )}

      {r.risk_factors?.length > 0 && (
        <Section title="Risk Factors" count={r.risk_factors.length}>
          <div className="flex flex-col gap-2">
            {r.risk_factors.map((rf, i) => (
              <div key={i} className="flex items-start gap-3">
                <span className={`text-xs px-2 py-0.5 rounded border font-medium capitalize whitespace-nowrap mt-0.5 ${SEVERITY_COLORS[rf.severity] || SEVERITY_COLORS.medium}`}>
                  {rf.severity}
                </span>
                <div>
                  <p className="text-slate-300 text-sm font-medium">{rf.factor}</p>
                  {rf.rationale && <p className="text-slate-500 text-xs mt-0.5">{rf.rationale}</p>}
                </div>
              </div>
            ))}
          </div>
        </Section>
      )}
    </div>
  );
}
