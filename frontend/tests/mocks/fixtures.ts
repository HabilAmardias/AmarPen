export const user = {
  id: 'user-1',
  username: 'admin',
  roles: ['Administrator', 'Analyst', 'Reviewer'],
  totp_enabled: true,
  disabled: false,
  created_at: '2026-01-01T12:00:00Z'
};

export const session = {
  user,
  csrf_token: 'csrf-token',
  session_id: 'session-1'
};

export const engagement = {
  id: 'eng-1',
  name: 'Acme external assessment',
  owner_id: 'user-1',
  status: 'READY',
  description: 'External black-box assessment',
  authorization_ref: 'AUTH-2026-01',
  authorization_valid: true,
  targets: ['example.com'],
  exclusions: ['admin.example.com'],
  window_start: '2026-01-01T00:00:00Z',
  window_end: '2026-02-01T00:00:00Z',
  access_profile: 'anonymous',
  model_profile: 'local-default',
  budgets: { requests_per_second: 5, burst: 5 },
  prohibited: ['destructive_actions'],
  business_context: { risk_owner: 'Security lead' },
  scope_version: 1,
  config_version: 2,
  risk_policy_id: 'policy-1',
  created_at: '2026-01-01T12:00:00Z',
  updated_at: '2026-01-02T12:00:00Z'
};

export const run = {
  id: 'run-1',
  engagement_id: 'eng-1',
  state: 'RUNNING',
  version: 2,
  release_id: 'release-1',
  initiated_by: 'user-1',
  reason: '',
  created_at: '2026-01-01T12:00:00Z',
  updated_at: '2026-01-01T12:05:00Z'
};

export const finding = {
  id: 'finding-1',
  engagement_id: 'eng-1',
  run_id: 'run-1',
  title: 'Reflected cross-site scripting',
  description: 'The search parameter reflects script without encoding.',
  affected_assets: ['example.com'],
  prerequisites: 'Authenticated none',
  expected_behavior: 'Input is encoded',
  actual_behavior: 'Payload is reflected',
  reproduction_steps: ['Open the search page', 'Submit the payload', 'Observe execution'],
  impact: 'Session compromise in a victim browser',
  remediation: 'Encode output and apply CSP',
  framework_refs: ['WSTG-INPV-01'],
  state: 'VALIDATED',
  verdict: 'VALIDATED',
  confidence: 'high',
  version: 2,
  latest_retest_outcome: 'STILL_OPEN',
  latest_retest_status: 'VALIDATED',
  created_at: '2026-01-01T12:00:00Z',
  updated_at: '2026-01-01T12:30:00Z'
};

export const assessment = {
  id: 'assessment-1',
  finding_id: 'finding-1',
  cvss_vector: 'CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:H/VI:H/VA:H/SC:H/SI:H/SA:N',
  cvss_score: 9.9,
  cvss_rating: 'Critical',
  cvss_rationale: { AV: 'network' },
  business_likelihood: 4,
  business_impact: 4,
  business_band: 'High',
  business_rationale: 'Customer data exposure',
  manual_severity: 'High',
  manual_reason: 'Compensating control present',
  manual_by: 'user-1',
  confidence: 'high',
  provisional: false,
  version: 3,
  history: [],
  created_at: '2026-01-01T12:00:00Z',
  updated_at: '2026-01-01T12:30:00Z'
};

export const evidence = {
  id: 'evidence-1',
  finding_id: 'finding-1',
  kind: 'request_response',
  storage_key: 'eng-1/finding-1/proof',
  sha256: 'abc123',
  classification: 'restricted',
  created_at: '2026-01-01T12:10:00Z'
};

export const coverage = {
  counts: { TESTED_NO_ISSUE_OBSERVED: 1, INCONCLUSIVE: 1 },
  records: [
    { id: 'coverage-1', target: 'example.com', scenario: 'WSTG-INFO-01', status: 'TESTED_NO_ISSUE_OBSERVED', reason: '' },
    { id: 'coverage-2', target: 'example.com', scenario: 'WSTG-INPV-01', status: 'INCONCLUSIVE', reason: 'Tool failed' }
  ]
};

export const reports = [
  {
    id: 'report-1',
    engagement_id: 'eng-1',
    version: 1,
    status: 'PREVIEW',
    pdf_key: '',
    sha256: '',
    reviewer_id: '',
    created_at: '2026-01-01T12:00:00Z'
  }
];

export const auditEvent = {
  event_id: 'event-1',
  occurred_at: '2026-01-01T12:00:00Z',
  recorded_at: '2026-01-01T12:00:00Z',
  actor_type: 'user',
  actor_id: 'user-1',
  action: 'engagement.created',
  resource: 'engagement:eng-1',
  asset: 'example.com',
  outcome: 'SUCCESS',
  correlation_id: 'corr-1',
  details: { name: 'Acme external assessment' }
};

export const prompts = [
  {
    id: 'prompt-1',
    key: 'agent-orchestrator',
    agent_role: 'orchestrator',
    purpose: 'Coordinates assessment work',
    state: 'PUBLISHED',
    version: 1,
    content_hash: 'hash-1',
    author_id: 'system',
    change_reason: 'Initial baseline',
    body: 'Act safely within scope.'
  }
];

export const releases = [
  {
    id: 'release-1',
    name: 'baseline-1',
    manifest: { orchestrator: 'prompt-1' },
    state: 'ACTIVE',
    version: 1,
    validated: true
  }
];

export const modelProfiles = [
  {
    id: 'profile-1',
    name: 'local-default',
    base_url: 'http://localhost:8080/v1',
    model: 'mock-pentest',
    data_boundary: 'on_premises',
    capabilities: ['chat', 'structured_outputs'],
    enabled: true
  }
];

export const riskPolicies = [
  { id: 'policy-1', name: 'Initial proposed matrix', version: 1, active: true, horizon: '12 months' }
];

export const users = [
  user,
  {
    id: 'user-2',
    username: 'analyst',
    roles: ['Analyst'],
    totp_enabled: true,
    disabled: false,
    created_at: '2026-01-01T12:00:00Z'
  }
];

export const scenarios = [
  {
    id: 'scenario-1',
    key: 'WSTG-INFO-01',
    version: '1.0',
    title: 'Information gathering',
    framework_refs: ['WSTG-INFO-01'],
    side_effects: ['read_only']
  }
];
