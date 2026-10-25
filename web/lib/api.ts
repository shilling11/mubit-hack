/** Typed client for the Redress API (FastAPI, app/main.py). */
export const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export type Answer = "yes" | "no" | "na" | "unsure";
export type Tier = "low" | "medium" | "high" | "critical";
export type QueueKind = "breach" | "analyst" | "audit" | "auto";

export interface Status {
  mubit: { base_url: string; key_set: boolean; model: string; reasoning_effort: string | null };
  deepgram_key_set: boolean;
  playbook_version: number;
  pending_corrections: number;
  mubit_calls: number;
  mubit_errors: number;
  training_examples_sent: number;
}

export interface ScorecardItem {
  id: string;
  label: string;
  kind: "critical" | "scored";
  weight: number;
  basis: string;
  guidance: string;
}

export interface Evidence {
  quote: string;
  start_s: number;
  speaker: string;
}

export interface ReviewItem {
  id: string;
  answer: Answer;
  reasoning: string;
  evidence: Evidence[];
  confidence: number;
  model_answer: Answer | null;
  label: string;
  kind: "critical" | "scored";
  weight: number;
  basis: string;
}

export interface Review {
  id: number;
  call_id: string;
  playbook_version: number;
  model: string;
  record_mode: string;
  request_id: string | null;
  served_by: string | null;
  latency_ms: number | null;
  tokens_in: number | null;
  tokens_out: number | null;
  score: number;
  pass: number;
  critical_fails: string[];
  risk_tier: Tier;
  issues_json: { item: string; issue: string; quote?: string }[];
  output_json: {
    complaint: { expressed: boolean; category: string; quote: string };
    vulnerability: { driver: string; quote: string }[];
    summary: string;
  };
  items_json: Record<string, Omit<ReviewItem, "label" | "kind" | "weight" | "basis">>;
  items?: ReviewItem[];
  error: string | null;
  created_at: number;
}

export interface Utterance {
  idx: number;
  speaker: "agent" | "customer";
  text: string;
  raw: string;
  start_s: number;
  end_s: number | null;
  confidence: number | null;
}

export interface QueueEntry {
  call_id: string;
  review_id: number;
  kind: QueueKind;
  reasons_json: string[];
  audit: number;
  due_at: number | null;
  done: number;
}

export interface Call {
  id: string;
  source: string;
  split: string;
  agent_name: string;
  audio_path: string | null;
  duration_s: number | null;
  stt_confidence: number | null;
  customer_name?: string | null;
  audio_muted?: number | null;
  status: string;
  error: string | null;
  created_at: number;
  utterances: Utterance[];
  review: Review | null;
  queue: QueueEntry | null;
  evaluation: { id: number; items_json: { id: string; ai: Answer; answer: Answer; agreed: boolean; reason: string }[] } | null;
}

export interface Wall {
  total: number;
  scored: number;
  sampled: number;
  breaches: number;
  to_analyst: number;
  tiles: { call_id: string; risk_tier: Tier | null; pass: number | null; queue: QueueKind | null; sampled: boolean; status: string }[];
}

export interface QueueRow extends QueueEntry {
  agent_name: string;
  split: string;
  risk_tier: Tier | null;
  score: number | null;
}

export interface Rule {
  correction_id: number;
  item_id: string;
  source: string;
  rule: string;
  applies_when: string;
  keywords: string[];
}

export interface Correction {
  id: number;
  call_id: string | null;
  item_id: string;
  before: string | null;
  after: string;
  reason: string;
  source: "analyst" | "seed";
  rule_json: { rule: string; applies_when: string; keywords: string[] } | null;
  created_at: number;
}

export interface Learning {
  playbook_version: number;
  versions: { version: number; created_at: number | null; correction_ids: number[]; rules_json: Rule[]; note: string }[];
  corrections: Correction[];
  agreement: { item_id: string; n: number; agreed: number; pct: number | null }[];
}

export interface Range {
  mean: number;
  min: number;
  max: number;
}

export interface CompareGroup {
  playbook_version: number;
  model: string;
  runs: number;
  label: string;
  run_ids: string[];
  n_items: number;
  metrics: Record<
    | "item_accuracy" | "system_critical_recall" | "model_critical_recall" | "false_negatives" | "critical_precision"
    | "human_queue_rate" | "complaint_recall" | "vulnerability_recall" | "latency_p50_ms" | "tokens",
    Range | null
  >;
  per_call: { call_id: string; items_correct: number; false_negatives: string[] }[];
}

export interface Run {
  id: string;
  label: string;
  split: string;
  playbook_version: number;
  status: string;
  total: number;
  done: number;
  error: string | null;
  created_at: number;
}

export interface Trace {
  id: number;
  ts: number;
  task: string;
  call_id: string | null;
  run_id: string | null;
  request_id: string | null;
  model_asked: string;
  served_by: string | null;
  record_mode: string;
  latency_ms: number | null;
  tokens_in: number | null;
  tokens_out: number | null;
  ok: number;
  error: string | null;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API}${path}`, {
    ...init,
    headers: init?.body && !(init.body instanceof FormData) ? { "Content-Type": "application/json" } : undefined,
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const j = await res.json();
      detail = typeof j.detail === "string" ? j.detail : JSON.stringify(j.detail);
    } catch {}
    throw new Error(detail);
  }
  return res.json() as Promise<T>;
}

const post = <T,>(path: string, body?: unknown) =>
  request<T>(path, { method: "POST", body: body === undefined ? undefined : JSON.stringify(body) });

export const api = {
  status: () => request<Status>("/api/status"),
  scorecard: () => request<{ bank: string; pass_mark: number; items: ScorecardItem[] }>("/api/scorecard"),
  wall: () => request<Wall>("/api/wall"),
  queue: () => request<QueueRow[]>("/api/queue"),
  call: (id: string) => request<Call>(`/api/calls/${id}`),
  audioUrl: (id: string) => `${API}/api/calls/${id}/audio`,
  upload: (audio: Blob, filename: string, agentName: string, customerName = "") => {
    const fd = new FormData();
    fd.append("audio", audio, filename);
    fd.append("agent_name", agentName);
    fd.append("customer_name", customerName);
    return request<{ call_id: string }>("/api/calls", { method: "POST", body: fd });
  },
  loadScript: (id: string) => post<{ call_id: string }>(`/api/demo/scripts/${id}`),
  rereview: (id: string, version?: number) =>
    post<Review>(`/api/calls/${id}/review${version === undefined ? "" : `?playbook_version=${version}`}`),
  swap: (id: string) => post<{ swapped: boolean }>(`/api/calls/${id}/swap-speakers`),
  flip: (id: string, idx: number) => post<{ idx: number; speaker: "agent" | "customer" }>(`/api/calls/${id}/utterances/${idx}/flip`),
  evaluate: (id: string, body: { review_id: number; items: { id: string; answer: Answer; reason: string }[]; comments?: string }) =>
    post<{ corrections: Correction[]; playbook_version: number; rules: Rule[] }>(`/api/calls/${id}/evaluation`, { analyst: "analyst", ...body }),
  learning: () => request<Learning>("/api/learning"),
  seed: () => post<{ loaded: number; playbook_version: number }>("/api/corrections/seed"),
  testRule: (correctionId: number, limit = 4) =>
    post<{ tested: string[]; changed: { call_id: string; item_id: string; before: Answer; after: Answer }[] }>(
      `/api/rules/${correctionId}/test?limit=${limit}`,
    ),
  compare: () => request<CompareGroup[]>("/api/compare"),
  runs: () => request<Run[]>("/api/runs"),
  startEval: (repeats = 3) => post<{ run_ids: string[]; versions: number[] }>("/api/eval", { repeats }),
  traces: (limit = 40) => request<Trace[]>(`/api/traces?limit=${limit}`),
  reset: () => post<{ cleared_live_calls: number }>("/api/demo/reset"),
};

export const pct = (v: number | null | undefined, d = 0) => (v == null ? "—" : `${(v * 100).toFixed(d)}%`);
export const secs = (ms: number | null | undefined) => (ms == null ? "—" : `${(ms / 1000).toFixed(1)}s`);
export const ts = (s: number) => {
  const m = Math.floor(s / 60);
  return `${m}:${String(Math.floor(s % 60)).padStart(2, "0")}`;
};
export const ago = (t: number) => {
  const s = Math.max(0, Date.now() / 1000 - t);
  return s < 60 ? `${Math.floor(s)}s ago` : s < 3600 ? `${Math.floor(s / 60)}m ago` : `${Math.floor(s / 3600)}h ago`;
};
