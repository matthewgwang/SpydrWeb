import type {
  AccountProfile,
  AlertBundle,
  CaseReport,
  GraphData,
  Transaction,
  TransactionFeedItem,
} from "../types";

const BASE = "/api";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json() as Promise<T>;
}

// Transactions
export const processTransaction = (tx: Partial<Transaction>) =>
  request<CaseReport>("/transactions/process", {
    method: "POST",
    body: JSON.stringify(tx),
  });

export const getTransactions = (limit = 50) =>
  request<TransactionFeedItem[]>(`/transactions?limit=${limit}`);

// Accounts
export const getAccountProfile = (id: string) =>
  request<AccountProfile>(`/accounts/${id}/profile`);

export const getAccounts = () =>
  request<AccountProfile[]>("/accounts");

// Reports
export const getReport = (id: string) =>
  request<CaseReport>(`/reports/${id}`);

export const getReports = (limit = 50) =>
  request<CaseReport[]>(`/reports?limit=${limit}`);

// Graph
export const getGraphData = () =>
  request<GraphData>("/graph/data");

export const getGraphNeighbors = (nodeId: string, depth = 1) =>
  request<GraphData>(`/graph/neighbors/${nodeId}?depth=${depth}`);

// Alerts
export const getAlertBundles = () =>
  request<AlertBundle[]>("/alerts/bundles");

// Feedback
export const submitFeedback = (payload: {
  report_id: string;
  action: string;
  fraud_type?: string;
  notes?: string;
}) =>
  request<{ status: string }>("/feedback", {
    method: "POST",
    body: JSON.stringify(payload),
  });

// Demo controls
export const startDemo = () =>
  request<{ status: string }>("/demo/start", { method: "POST" });

export const injectFraud = (scenario: string) =>
  request<Transaction>(`/demo/inject-fraud/${scenario}`, { method: "POST" });

export const setMode = (mode: "pipeline" | "agentic") =>
  request<{ mode: string }>("/demo/mode", {
    method: "POST",
    body: JSON.stringify({ mode }),
  });
