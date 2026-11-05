export type Role = 'Administrator' | 'Analyst' | 'Reviewer' | 'Viewer';

export interface User {
  id: string;
  username: string;
  roles: Role[];
  totp_enabled: boolean;
  disabled: boolean;
  created_at: string;
}

export interface SessionInfo {
  user: User;
  csrf_token: string;
  session_id: string;
}

export interface Engagement {
  id: string;
  name: string;
  owner_id: string;
  status: string;
  description: string;
  authorization_ref: string;
  authorization_valid: boolean;
  targets: string[];
  exclusions: string[];
  window_start: string | null;
  window_end: string | null;
  access_profile: string;
  model_profile: string;
  budgets: Record<string, number>;
  prohibited: string[];
  business_context: Record<string, unknown>;
  scope_version: number;
  config_version: number;
  risk_policy_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface Run {
  id: string;
  engagement_id: string;
  state: string;
  version: number;
  release_id: string | null;
  initiated_by: string;
  reason: string;
  created_at: string;
  updated_at: string;
}

export interface Finding {
  id: string;
  engagement_id: string;
  run_id: string | null;
  title: string;
  description: string;
  affected_assets: string[];
  prerequisites: string;
  expected_behavior: string;
  actual_behavior: string;
  reproduction_steps: string[];
  impact: string;
  remediation: string;
  framework_refs: string[];
  state: string;
  verdict: string;
  confidence: string;
  version: number;
  latest_retest_outcome: string;
  latest_retest_status: string;
  created_at: string;
  updated_at: string;
}

export interface Evidence {
  id: string;
  finding_id: string;
  kind: string;
  storage_key: string;
  sha256: string;
  classification: string;
  created_at: string;
}

export interface Assessment {
  id: string;
  finding_id: string;
  cvss_vector: string;
  cvss_score: number;
  cvss_rating: string;
  cvss_rationale: Record<string, string>;
  business_likelihood: number;
  business_impact: number;
  business_band: string;
  business_rationale: string;
  manual_severity: string;
  manual_reason: string;
  manual_by: string;
  confidence: string;
  provisional: boolean;
  version: number;
  history: unknown[];
  created_at: string;
  updated_at: string;
}

export interface CoverageRecord {
  id: string;
  target: string;
  scenario: string;
  status: string;
  reason: string;
}

export interface Scenario {
  id: string;
  key: string;
  version: string;
  title: string;
  framework_refs: string[];
  side_effects: string[];
}

export interface ReportSnapshot {
  id: string;
  engagement_id: string;
  version: number;
  status: string;
  pdf_key: string;
  sha256: string;
  reviewer_id: string;
  created_at: string;
}

export interface AuditEvent {
  event_id: string;
  occurred_at: string;
  recorded_at: string;
  actor_type: string;
  actor_id: string;
  action: string;
  resource: string;
  asset: string;
  outcome: string;
  correlation_id: string;
  details: Record<string, unknown>;
}

export interface SystemPrompt {
  id: string;
  key: string;
  agent_role: string;
  purpose: string;
  state: string;
  version: number;
  content_hash: string;
  author_id: string;
  change_reason: string;
  body?: string;
}

export interface PromptRelease {
  id: string;
  name: string;
  manifest: Record<string, string>;
  state: string;
  version: number;
  validated: boolean;
}

export interface ModelProfile {
  id: string;
  name: string;
  base_url: string;
  model: string;
  data_boundary: string;
  capabilities: string[];
  enabled: boolean;
}

export interface RiskPolicy {
  id: string;
  name: string;
  version: number;
  active: boolean;
  horizon: string;
}

export interface RetestAttempt {
  id: string;
  engagement_id: string;
  run_id: string;
  finding_ids: string[];
  outcomes: Record<string, string>;
  notes: string;
  state: string;
  created_at: string;
}

export interface ListResponse<T> {
  items: T[];
  meta?: { page: number; page_size: number; total: number; pages: number };
}

export interface ApiErrorBody {
  error: {
    code: string;
    message: string;
    details?: Record<string, unknown>;
    correlation_id?: string;
  };
}


export interface AgentTask {
  id: string;
  run_id: string;
  role: string;
  kind: string;
  state: string;
  asset: string;
  attempt: number;
  outcome: string;
  ownership_key: string;
  result_id: string;
}

export interface AgentTaskResult {
  id: string;
  task_id: string;
  role: string;
  status: string;
  limitations: string[];
  stale: boolean;
}

export interface AgentProposal {
  id: string;
  task_id: string;
  kind: string;
  status: string;
  decision_reason: string;
}

export interface AssetRecord {
  id: string;
  kind: string;
  value: string;
}

export interface AgentActivity {
  tasks: AgentTask[];
  results: AgentTaskResult[];
  proposals: AgentProposal[];
  assets: AssetRecord[];
}
