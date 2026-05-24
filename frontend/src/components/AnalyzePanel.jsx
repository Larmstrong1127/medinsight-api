import { useState } from "react";
import { createDocument, analyzeDocument } from "../api/client";

const ANALYSIS_TYPES = [
  { value: "full_analysis", label: "Full Analysis" },
  { value: "summarize", label: "Summarize" },
  { value: "extract_diagnoses", label: "Extract Diagnoses" },
  { value: "extract_medications", label: "Extract Medications" },
  { value: "risk_assessment", label: "Risk Assessment" },
];

const DOCUMENT_TYPES = [
  { value: "admission_note", label: "Admission Note" },
  { value: "discharge_summary", label: "Discharge Summary" },
  { value: "progress_note", label: "Progress Note" },
  { value: "radiology_report", label: "Radiology Report" },
  { value: "lab_report", label: "Lab Report" },
  { value: "operative_note", label: "Operative Note" },
];

const SAMPLE_NOTE = `Patient: Synthetic Male, Age 67. Chief complaint: chest pain and dyspnea x2 days.
PMH: HTN, T2DM, hyperlipidemia.
Medications: Metformin 1000mg BID, Atorvastatin 40mg QD, Amlodipine 5mg QD.
Vitals: BP 158/94, HR 88, RR 18, SpO2 94%.
EKG: ST depression leads V4-V6. Troponin I 0.8 ng/mL (elevated).
Assessment: NSTEMI. Plan: Heparin drip, aspirin 325mg, clopidogrel 600mg loading, cardiology consult.`;

export default function AnalyzePanel({ onResult, onLoading }) {
  const [content, setContent] = useState("");
  const [patientId, setPatientId] = useState("pt-demo-001");
  const [docType, setDocType] = useState("admission_note");
  const [analysisType, setAnalysisType] = useState("full_analysis");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleAnalyze = async () => {
    if (!content.trim()) return;
    setLoading(true);
    setError(null);
    onLoading(true);
    try {
      const docRes = await createDocument({
        content,
        patient_id: patientId,
        document_type: docType,
      });
      const analysisRes = await analyzeDocument(docRes.data.id, analysisType);
      onResult(analysisRes.data);
    } catch (err) {
      setError(err.response?.data?.detail || "Something went wrong.");
    } finally {
      setLoading(false);
      onLoading(false);
    }
  };

  return (
    <div className="bg-navy-800 border border-slate-700/50 rounded-xl p-6 flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <h2 className="text-white font-semibold text-base">Clinical Note</h2>
        <button
          onClick={() => setContent(SAMPLE_NOTE)}
          className="text-xs text-blue-400 hover:text-blue-300 transition-colors"
        >
          Load sample note
        </button>
      </div>

      <textarea
        value={content}
        onChange={(e) => setContent(e.target.value)}
        placeholder="Paste a clinical note here..."
        rows={10}
        className="w-full bg-navy-900 border border-slate-700/50 rounded-lg p-3 text-sm text-slate-300 placeholder-slate-600 focus:outline-none focus:border-blue-500/50 resize-none font-mono"
      />

      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="text-xs text-slate-500 mb-1 block">Patient ID</label>
          <input
            value={patientId}
            onChange={(e) => setPatientId(e.target.value)}
            className="w-full bg-navy-900 border border-slate-700/50 rounded-lg px-3 py-2 text-sm text-slate-300 focus:outline-none focus:border-blue-500/50"
          />
        </div>
        <div>
          <label className="text-xs text-slate-500 mb-1 block">Document Type</label>
          <select
            value={docType}
            onChange={(e) => setDocType(e.target.value)}
            className="w-full bg-navy-900 border border-slate-700/50 rounded-lg px-3 py-2 text-sm text-slate-300 focus:outline-none focus:border-blue-500/50"
          >
            {DOCUMENT_TYPES.map((t) => (
              <option key={t.value} value={t.value}>{t.label}</option>
            ))}
          </select>
        </div>
      </div>

      <div>
        <label className="text-xs text-slate-500 mb-2 block">Analysis Type</label>
        <div className="flex flex-wrap gap-2">
          {ANALYSIS_TYPES.map((t) => (
            <button
              key={t.value}
              onClick={() => setAnalysisType(t.value)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                analysisType === t.value
                  ? "bg-blue-500/20 border border-blue-500/50 text-blue-300"
                  : "bg-navy-900 border border-slate-700/50 text-slate-400 hover:text-slate-300"
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>
      </div>

      {error && (
        <p className="text-red-400 text-xs bg-red-500/10 border border-red-500/20 rounded-lg px-3 py-2">
          {error}
        </p>
      )}

      <button
        onClick={handleAnalyze}
        disabled={loading || !content.trim()}
        className="w-full py-2.5 rounded-lg bg-blue-600 hover:bg-blue-500 disabled:bg-slate-700 disabled:text-slate-500 text-white text-sm font-medium transition-colors"
      >
        {loading ? "Analyzing..." : "Analyze"}
      </button>
    </div>
  );
}
