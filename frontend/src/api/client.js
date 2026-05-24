import axios from "axios";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";
const API_KEY = import.meta.env.VITE_API_KEY || "dev-key-change-me-in-production";

const client = axios.create({
  baseURL: API_BASE,
  headers: { "X-API-Key": API_KEY, "Content-Type": "application/json" },
});

export const createDocument = (payload) => client.post("/api/v1/documents", payload);
export const listDocuments = (patientId) =>
  client.get("/api/v1/documents", { params: patientId ? { patient_id: patientId } : {} });
export const analyzeDocument = (documentId, analysisType, context) =>
  client.post("/api/v1/analysis", { document_id: documentId, analysis_type: analysisType, context });
export const agentQuery = (query, patientId) =>
  client.post("/api/v1/agent/query", { query, patient_id: patientId || undefined });
export const getAuditLogs = () => client.get("/api/v1/audit/logs?limit=20");
