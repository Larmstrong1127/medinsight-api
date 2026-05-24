import { useState, useEffect } from "react";
import { getAuditLogs } from "../api/client";

const OUTCOME_COLORS = {
  success: "text-emerald-400",
  failure: "text-red-400",
  denied: "text-yellow-400",
};

export default function AuditLog({ refreshTrigger }) {
  const [logs, setLogs] = useState([]);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    if (!open) return;
    getAuditLogs()
      .then((res) => setLogs(res.data.logs))
      .catch(() => {});
  }, [open, refreshTrigger]);

  return (
    <div className="bg-navy-800 border border-slate-700/50 rounded-xl overflow-hidden">
      <button
        onClick={() => setOpen((v) => !v)}
        className="w-full px-6 py-4 flex items-center justify-between hover:bg-navy-700/30 transition-colors"
      >
        <div className="flex items-center gap-3">
          <span className="text-slate-300 font-medium text-sm">Audit Log</span>
          <span className="text-xs text-slate-500 bg-navy-900 px-2 py-0.5 rounded-full border border-slate-700/50">
            {logs.length} entries
          </span>
        </div>
        <span className="text-slate-500 text-xs">{open ? "▲ collapse" : "▼ expand"}</span>
      </button>

      {open && (
        <div className="border-t border-slate-700/50 overflow-x-auto">
          {logs.length === 0 ? (
            <p className="text-slate-500 text-sm text-center py-6">No audit entries yet</p>
          ) : (
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-slate-700/50 bg-navy-900/50">
                  {["Time", "Action", "Resource", "Key", "IP", "Outcome"].map((h) => (
                    <th key={h} className="text-left text-slate-500 px-4 py-2.5 font-medium">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {logs.map((log) => (
                  <tr key={log.id} className="border-b border-slate-700/30 hover:bg-navy-700/20">
                    <td className="px-4 py-2.5 text-slate-500 whitespace-nowrap">
                      {new Date(log.timestamp).toLocaleTimeString()}
                    </td>
                    <td className="px-4 py-2.5 text-slate-300 font-mono">{log.action}</td>
                    <td className="px-4 py-2.5 text-slate-500 font-mono truncate max-w-[120px]">
                      {log.resource_id || "—"}
                    </td>
                    <td className="px-4 py-2.5 text-slate-500 font-mono">{log.api_key_prefix}…</td>
                    <td className="px-4 py-2.5 text-slate-500">{log.ip_address}</td>
                    <td className={`px-4 py-2.5 font-medium ${OUTCOME_COLORS[log.outcome] || "text-slate-400"}`}>
                      {log.outcome}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}
    </div>
  );
}
