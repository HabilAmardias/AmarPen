import type {
  ApiErrorBody,
  Assessment,
  AgentActivity,
  AuditEvent,
  CoverageRecord,
  Engagement,
  Evidence,
  Finding,
  ListResponse,
  ModelProfile,
  McpManifestSummary,
  McpServerSummary,
  ModelProfileOption,
  PromptRelease,
  ReportSnapshot,
  RetestAttempt,
  RiskPolicy,
  Run,
  Scenario,
  SessionInfo,
  SystemPrompt,
  User
} from './types';

const BASE = import.meta.env?.VITE_API_BASE ?? '/api/v1';

export class ApiError extends Error {
  status: number;
  code: string;
  details: Record<string, unknown>;
  correlationId: string;

  constructor(status: number, body: ApiErrorBody | null, fallback = 'Request failed') {
    const error = body?.error;
    super(error?.message ?? fallback);
    this.name = 'ApiError';
    this.status = status;
    this.code = error?.code ?? 'request_failed';
    this.details = error?.details ?? {};
    this.correlationId = error?.correlation_id ?? '';
  }
}

function url(path: string): string {
  if (BASE.startsWith('http')) {
    return `${BASE}${path}`;
  }
  const origin = typeof window !== 'undefined' ? window.location.origin : 'http://localhost';
  return new URL(`${BASE}${path}`, origin).toString();
}

function cookie(name: string): string {
  if (typeof document === 'undefined') return '';
  return (
    document.cookie
      .split(';')
      .map((item) => item.trim())
      .find((item) => item.startsWith(`${name}=`))
      ?.split('=')
      .slice(1)
      .join('=') ?? ''
  );
}

interface RequestOptions {
  method?: string;
  body?: unknown;
  signal?: AbortSignal;
  formData?: FormData;
  raw?: boolean;
}

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const method = options.method ?? 'GET';
  const headers: Record<string, string> = {};
  const init: RequestInit = {
    method,
    credentials: 'include',
    headers,
    signal: options.signal
  };
  if (options.formData) {
    init.body = options.formData;
  } else if (options.body !== undefined) {
    headers['Content-Type'] = 'application/json';
    init.body = JSON.stringify(options.body);
  }
  if (!['GET', 'HEAD', 'OPTIONS'].includes(method)) {
    const csrf = cookie('pt_csrf');
    if (csrf) headers['X-CSRF-Token'] = csrf;
  }
  const response = await fetch(url(path), init);
  if (options.raw) {
    return response as unknown as T;
  }
  if (response.status === 204) {
    return undefined as T;
  }
  const contentType = response.headers.get('content-type') ?? '';
  const payload = contentType.includes('application/json') ? await response.json() : await response.text();
  if (!response.ok) {
    throw new ApiError(response.status, typeof payload === 'object' ? payload : null);
  }
  return payload as T;
}

export const api = {
  auth: {
    session: () => request<SessionInfo>('/auth/session'),
    login: (username: string, password: string) =>
      request<{ user: User; requires_totp: boolean; requires_enrollment: boolean; next: string }>('/auth/login', {
        method: 'POST',
        body: { username, password }
      }),
    totp: (code: string) =>
      request<{ user: User; requires_enrollment: boolean; next: string }>('/auth/totp', {
        method: 'POST',
        body: { code }
      }),
    logout: () => request<void>('/auth/logout', { method: 'POST' }),
    enrollmentStart: () =>
      request<{ secret: string; provisioning_uri: string }>('/auth/enrollment/start', { method: 'POST' }),
    enrollmentVerify: (code: string) =>
      request<{ user: User; recovery_codes: string[] }>('/auth/enrollment/verify', {
        method: 'POST',
        body: { code }
      }),
    recovery: (username: string, recovery_code: string, new_password: string) =>
      request<void>('/auth/recovery', {
        method: 'POST',
        body: { username, recovery_code, new_password }
      }),
    changePassword: (current_password: string, new_password: string) =>
      request<void>('/auth/password', { method: 'POST', body: { current_password, new_password } })
  },
  access: {
    users: () => request<ListResponse<User>>('/access/users'),
    createUser: (username: string, roles: string[]) =>
      request<{ user: User; temporary_password: string }>('/access/users', {
        method: 'POST',
        body: { username, roles }
      }),
    updateRoles: (id: string, roles: string[]) =>
      request<{ user: User }>(`/access/users/${id}/roles`, { method: 'PUT', body: { roles } }),
    disable: (id: string, disabled: boolean, reason = '') =>
      request<{ user: User }>(`/access/users/${id}/disabled`, {
        method: 'PUT',
        body: { disabled, reason }
      }),
    resetMfa: (id: string, reason = '') =>
      request<{ user: User }>(`/access/users/${id}/reset-mfa?reason=${encodeURIComponent(reason)}`, {
        method: 'POST'
      }),
    resetPassword: (id: string, reason = '') =>
      request<{ temporary_password: string }>(
        `/access/users/${id}/reset-password?reason=${encodeURIComponent(reason)}`,
        { method: 'POST' }
      )
  },
  engagements: {
    list: () => request<ListResponse<Engagement>>('/engagements'),
    quickStart: (payload: Record<string, unknown>) =>
      request<Engagement>('/engagements/quick-start', { method: 'POST', body: payload }),
    authorization: (id: string) =>
      request<{ valid: boolean; reason: string; attestation: Record<string, unknown> | null; attestation_text: string }>(
        `/engagements/${id}/authorization`
      ),
    attest: (id: string) =>
      request<Record<string, unknown>>(`/engagements/${id}/attest`, { method: 'POST', body: {} }),
    get: (id: string) => request<Engagement>(`/engagements/${id}`),
    create: (payload: Record<string, unknown>) =>
      request<Engagement>('/engagements', { method: 'POST', body: payload }),
    update: (id: string, payload: Record<string, unknown>) =>
      request<Engagement>(`/engagements/${id}`, { method: 'PUT', body: payload }),
    readiness: (id: string) =>
      request<{ ready: boolean; checks: Array<{ name: string; passed: boolean; message: string; blocking: boolean }>; blocking: string[] }>(
        `/engagements/${id}/readiness`
      ),
    plan: (id: string) =>
      request<{ selected: Scenario[]; skipped: Array<{ scenario: string; reasons: string[] }> }>(`/engagements/${id}/plan`)
  },
  runs: {
    list: (engagementId: string) => request<ListResponse<Run>>(`/runs/engagements/${engagementId}`),
    get: (id: string) => request<Run>(`/runs/${id}`),
    start: (engagementId: string, idempotency_key: string, reason = '') =>
      request<Run>(`/runs/engagements/${engagementId}/start`, {
        method: 'POST',
        body: { idempotency_key, reason }
      }),
    pause: (id: string, idempotency_key: string) =>
      request<Run>(`/runs/${id}/pause`, { method: 'POST', body: { idempotency_key } }),
    resume: (id: string, idempotency_key: string) =>
      request<Run>(`/runs/${id}/resume`, { method: 'POST', body: { idempotency_key } }),
    stop: (id: string, idempotency_key: string, reason = '') =>
      request<Run>(`/runs/${id}/stop`, { method: 'POST', body: { idempotency_key, reason } }),
    agents: (id: string) => request<AgentActivity>(`/runs/${id}/agents`)
  },
  testing: {
    scenarios: () => request<ListResponse<Scenario>>('/testing/scenarios'),
    coverage: (engagementId: string) =>
      request<{ counts: Record<string, number>; records: CoverageRecord[] }>(
        `/testing/engagements/${engagementId}/coverage`
      )
  },
  findings: {
    list: (engagementId: string, state = '') =>
      request<ListResponse<Finding>>(`/engagements/${engagementId}/findings${state ? `?state=${state}` : ''}`),
    get: (id: string) =>
      request<{ finding: Finding; evidence: Evidence[]; assessment: Assessment | null; retests: RetestAttempt[] }>(
        `/findings/${id}`
      ),
    create: (engagementId: string, payload: Record<string, unknown>) =>
      request<Finding>(`/engagements/${engagementId}/findings`, { method: 'POST', body: payload }),
    edit: (id: string, payload: Record<string, unknown>) =>
      request<Finding>(`/findings/${id}`, { method: 'PUT', body: payload }),
    validate: (id: string, verdict: string, reason: string) =>
      request<Finding>(`/findings/${id}/validate`, { method: 'POST', body: { verdict, reason } }),
    review: (id: string, decision: string, reason = '') =>
      request<Finding>(`/findings/${id}/review`, { method: 'POST', body: { decision, reason } }),
    addEvidence: (id: string, kind: string, file: File) => {
      const form = new FormData();
      form.set('kind', kind);
      form.set('file', file);
      return request<Evidence>(`/findings/${id}/evidence`, { method: 'POST', formData: form });
    },
    evidenceUrl: (id: string) => url(`/evidence/${id}`),
    retests: (engagementId: string) => request<ListResponse<RetestAttempt>>(`/engagements/${engagementId}/retests`),
    startRetest: (engagementId: string, finding_ids: string[], notes: string, idempotency_key: string) =>
      request<RetestAttempt>(`/engagements/${engagementId}/retests`, {
        method: 'POST',
        body: { finding_ids, notes, idempotency_key }
      }),
    recordRetest: (retestId: string, finding_id: string, outcome: string, rationale: string, file?: File) => {
      const form = new FormData();
      form.set('finding_id', finding_id);
      form.set('outcome', outcome);
      form.set('rationale', rationale);
      if (file) form.set('file', file);
      return request<RetestAttempt>(`/retests/${retestId}/outcomes`, { method: 'POST', formData: form });
    }
  },
  scoring: {
    get: (findingId: string) => request<{ assessment: Assessment | null }>(`/findings/${findingId}/assessment`),
    cvss: (findingId: string, vector: string, rationale: Record<string, string>, expected_version?: number) =>
      request<Assessment>(`/findings/${findingId}/assessment/cvss`, {
        method: 'PUT',
        body: { vector, rationale, expected_version }
      }),
    override: (findingId: string, severity: string, reason: string) =>
      request<Assessment>(`/findings/${findingId}/assessment/override`, {
        method: 'POST',
        body: { severity, reason }
      }),
    restore: (findingId: string) =>
      request<Assessment>(`/findings/${findingId}/assessment/restore`, { method: 'POST' }),
    businessRisk: (findingId: string, likelihood: number, impact: number, rationale: string) =>
      request<Assessment>(`/findings/${findingId}/assessment/business-risk`, {
        method: 'PUT',
        body: { likelihood, impact, rationale }
      })
  },
  prompts: {
    list: (includeBodies = false) =>
      request<ListResponse<SystemPrompt>>(`/prompts${includeBodies ? '?include_bodies=true' : ''}`),
    get: (id: string) => request<SystemPrompt>(`/prompts/${id}`),
    create: (payload: Record<string, unknown>) => request<SystemPrompt>('/prompts', { method: 'POST', body: payload }),
    update: (id: string, payload: Record<string, unknown>) =>
      request<SystemPrompt>(`/prompts/${id}`, { method: 'PUT', body: payload }),
    validate: (id: string) =>
      request<{ passed: boolean; checks: Record<string, boolean> }>(`/prompts/${id}/validate`, { method: 'POST' }),
    publish: (id: string) => request<SystemPrompt>(`/prompts/${id}/publish`, { method: 'POST' }),
    releases: () => request<ListResponse<PromptRelease>>('/prompts/releases/all'),
    createRelease: (name: string, manifest: Record<string, string>) =>
      request<PromptRelease>('/prompts/releases', { method: 'POST', body: { name, manifest } }),
    validateRelease: (id: string) =>
      request<PromptRelease>(`/prompts/releases/${id}/validate`, { method: 'POST' }),
    activateRelease: (id: string, reason = '') =>
      request<PromptRelease>(`/prompts/releases/${id}/activate`, { method: 'POST', body: { reason } })
  },
  audit: {
    events: (query = '') => request<ListResponse<AuditEvent>>(`/audit/events${query ? `?${query}` : ''}`),
    exportUrl: (format = 'json') => url(`/audit/export?format=${format}`)
  },
  reports: {
    list: (engagementId: string) => request<ListResponse<ReportSnapshot>>(`/engagements/${engagementId}/reports`),
    create: (engagementId: string, partial = false) =>
      request<ReportSnapshot>(`/engagements/${engagementId}/reports`, { method: 'POST', body: { partial } }),
    approve: (id: string) => request<ReportSnapshot>(`/reports/${id}/approve`, { method: 'POST' }),
    render: (id: string) => request<ReportSnapshot>(`/reports/${id}/render`, { method: 'POST' }),
    previewUrl: (id: string) => url(`/reports/${id}/preview`),
    downloadUrl: (id: string) => url(`/reports/${id}/download`)
  },
  modelProfiles: {
    options: () => request<ListResponse<ModelProfileOption>>('/model-profiles')
  },
  admin: {
    modelProfiles: () => request<ListResponse<ModelProfile>>('/admin/model-profiles'),
    createModelProfile: (payload: Record<string, unknown>) =>
      request<ModelProfile>('/admin/model-profiles', { method: 'POST', body: payload }),
    updateModelProfile: (id: string, payload: Record<string, unknown>) =>
      request<ModelProfile>(`/admin/model-profiles/${id}`, { method: 'PUT', body: payload }),
    testModelProfile: (id: string) =>
      request<ModelProfile>(`/admin/model-profiles/${id}/test`, { method: 'POST' }),
    riskPolicies: () => request<ListResponse<RiskPolicy>>('/admin/risk-policies'),
    createRiskPolicy: (name: string) =>
      request<RiskPolicy>('/admin/risk-policies', { method: 'POST', body: { name } }),
    activateRiskPolicy: (id: string) =>
      request<RiskPolicy>(`/admin/risk-policies/${id}/activate`, { method: 'POST' }),
    settings: () => request<ListResponse<{ id: string; key: string; value: Record<string, unknown>; version: number }>>('/admin/settings'),
    updateSetting: (key: string, value: Record<string, unknown>) =>
      request<{ key: string }>(`/admin/settings/${key}`, { method: 'PUT', body: { value } }),
    mcpServers: () => request<{ items: McpServerSummary[] }>('/admin/mcp/servers'),
    createMcpServer: (payload: Record<string, unknown>) =>
      request<McpServerSummary>('/admin/mcp/servers', { method: 'POST', body: payload }),
    updateMcpServer: (stableId: string, payload: Record<string, unknown>) =>
      request<McpServerSummary>(`/admin/mcp/servers/${stableId}`, { method: 'PUT', body: payload }),
    revokeMcpServer: (stableId: string, reason: string) =>
      request<McpServerSummary>(`/admin/mcp/servers/${stableId}/revoke`, { method: 'POST', body: { reason } }),
    validateMcpManifest: (manifestId: string) =>
      request<McpManifestSummary>(`/admin/mcp/manifests/${manifestId}/validate`, { method: 'POST' }),
    revokeMcpManifest: (manifestId: string, reason: string) =>
      request<McpManifestSummary>(`/admin/mcp/manifests/${manifestId}/revoke`, { method: 'POST', body: { reason } }),
    discoverMcpServer: (stableId: string) =>
      request<McpManifestSummary>(`/admin/mcp/servers/${stableId}/discover`, { method: 'POST' }),
    activateMcpManifest: (manifestId: string) =>
      request<McpManifestSummary>(`/admin/mcp/manifests/${manifestId}/activate`, { method: 'POST' }),
    mcpReady: () => request<{ ready: boolean; checks: Array<{ name: string; passed: boolean; blocking: boolean; message: string }> }>('/admin/mcp/ready'),
    health: () => request<{ status: string; checks: Record<string, boolean> }>('/admin/health')
  }
};
