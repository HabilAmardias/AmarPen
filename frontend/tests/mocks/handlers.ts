import { http, HttpResponse } from 'msw';
import * as fixtures from './fixtures';

const json = (data: unknown, status = 200) => HttpResponse.json(data as never, { status });
const list = (items: unknown[]) => json({ items, meta: { page: 1, page_size: 50, total: items.length, pages: 1 } });

export const handlers = [
  http.get('*/api/v1/auth/session', () => json(fixtures.session)),
  http.post('*/api/v1/auth/login', () => json({ user: fixtures.user, requires_totp: true, requires_enrollment: false, next: 'totp' })),
  http.post('*/api/v1/auth/totp', () => json({ user: fixtures.user, requires_enrollment: false, next: 'session' })),
  http.post('*/api/v1/auth/logout', () => new HttpResponse(null, { status: 204 })),
  http.post('*/api/v1/auth/enrollment/start', () =>
    json({ secret: 'JBSWY3DPEHPK3PXP', provisioning_uri: 'otpauth://totp/ai-pentest:admin?secret=JBSWY3DPEHPK3PXP' })
  ),
  http.post('*/api/v1/auth/enrollment/verify', () =>
    json({ user: { ...fixtures.user, totp_enabled: true }, recovery_codes: ['alpha-code', 'beta-code'] })
  ),
  http.post('*/api/v1/auth/recovery', () => new HttpResponse(null, { status: 204 })),
  http.post('*/api/v1/auth/password', () => new HttpResponse(null, { status: 204 })),

  http.get('*/api/v1/engagements', () => list([fixtures.engagement])),
  http.post('*/api/v1/engagements', () => json(fixtures.engagement, 201)),
  http.get('*/api/v1/engagements/:id', () => json(fixtures.engagement)),
  http.put('*/api/v1/engagements/:id', () => json(fixtures.engagement)),
  http.get('*/api/v1/engagements/:id/readiness', () =>
    json({
      ready: true,
      checks: [
        { name: 'authorization', passed: true, message: 'Authorization is valid', blocking: true },
        { name: 'storage', passed: true, message: 'Evidence storage is healthy', blocking: true }
      ],
      blocking: []
    })
  ),
  http.get('*/api/v1/engagements/:id/plan', () =>
    json({ selected: fixtures.scenarios, skipped: [{ scenario: 'WSTG-BUSL-01', reasons: ['No accounts'] }] })
  ),

  http.get('*/api/v1/runs/engagements/:id', () => list([fixtures.run])),
  http.get('*/api/v1/runs/:id', () => json(fixtures.run)),
  http.get('*/api/v1/runs/:id/agents', () => json({ tasks: [], results: [], proposals: [], assets: [] })),
  http.post('*/api/v1/runs/engagements/:id/start', () => json({ ...fixtures.run, state: 'QUEUED' }, 202)),
  http.post('*/api/v1/runs/:id/pause', () => json({ ...fixtures.run, state: 'PAUSING' }, 202)),
  http.post('*/api/v1/runs/:id/resume', () => json({ ...fixtures.run, state: 'RUNNING' }, 202)),
  http.post('*/api/v1/runs/:id/stop', () => json({ ...fixtures.run, state: 'STOPPING' }, 202)),

  http.get('*/api/v1/testing/scenarios', () => list(fixtures.scenarios)),
  http.get('*/api/v1/testing/engagements/:id/coverage', () => json(fixtures.coverage)),

  http.get('*/api/v1/engagements/:id/findings', () => list([fixtures.finding])),
  http.post('*/api/v1/engagements/:id/findings', () => json(fixtures.finding, 201)),
  http.get('*/api/v1/findings/:id', () =>
    json({ finding: fixtures.finding, evidence: [fixtures.evidence], assessment: fixtures.assessment, retests: [] })
  ),
  http.put('*/api/v1/findings/:id', () => json(fixtures.finding)),
  http.post('*/api/v1/findings/:id/validate', () => json({ ...fixtures.finding, state: 'VALIDATED' })),
  http.post('*/api/v1/findings/:id/review', () => json({ ...fixtures.finding, state: 'REVIEWED' })),
  http.post('*/api/v1/findings/:id/evidence', () => json(fixtures.evidence, 201)),
  http.get('*/api/v1/evidence/:id', () => new HttpResponse('proof', { status: 200 })),
  http.get('*/api/v1/findings/:id/assessment', () => json({ assessment: fixtures.assessment })),
  http.put('*/api/v1/findings/:id/assessment/cvss', () => json(fixtures.assessment)),
  http.post('*/api/v1/findings/:id/assessment/override', () => json(fixtures.assessment)),
  http.post('*/api/v1/findings/:id/assessment/restore', () => json(fixtures.assessment)),
  http.put('*/api/v1/findings/:id/assessment/business-risk', () => json(fixtures.assessment)),
  http.post('*/api/v1/findings/:id/assessment/reassess', () => json(fixtures.assessment)),
  http.get('*/api/v1/engagements/:id/retests', () => list([])),
  http.post('*/api/v1/engagements/:id/retests', () =>
    json(
      {
        id: 'retest-1',
        engagement_id: 'eng-1',
        run_id: 'run-retest',
        finding_ids: ['finding-1'],
        outcomes: { 'finding-1': 'INCONCLUSIVE' },
        notes: 'Retest',
        state: 'RUNNING',
        created_at: '2026-01-01T12:00:00Z'
      },
      202
    )
  ),
  http.post('*/api/v1/retests/:id/outcomes', () =>
    json({ id: 'retest-1', engagement_id: 'eng-1', run_id: 'run-retest', finding_ids: ['finding-1'], outcomes: { 'finding-1': 'FIXED' }, notes: '', state: 'COMPLETED', created_at: '2026-01-01T12:00:00Z' })
  ),

  http.get('*/api/v1/prompts', ({ request }) => {
    const includeBodies = new URL(request.url).searchParams.get('include_bodies') === 'true';
    return list(fixtures.prompts.map((prompt) => (includeBodies ? prompt : { ...prompt, body: undefined })));
  }),
  http.get('*/api/v1/prompts/releases/all', () => list(fixtures.releases)),
  http.get('*/api/v1/prompts/:id', () => json(fixtures.prompts[0])),
  http.post('*/api/v1/prompts', () => json(fixtures.prompts[0], 201)),
  http.put('*/api/v1/prompts/:id', () => json(fixtures.prompts[0])),
  http.post('*/api/v1/prompts/:id/validate', () => json({ passed: true, checks: { body_present: true } })),
  http.post('*/api/v1/prompts/:id/publish', () => json(fixtures.prompts[0])),
  http.post('*/api/v1/prompts/releases', () => json(fixtures.releases[0], 201)),
  http.post('*/api/v1/prompts/releases/:id/validate', () => json(fixtures.releases[0])),
  http.post('*/api/v1/prompts/releases/:id/activate', () => json(fixtures.releases[0])),

  http.get('*/api/v1/audit/events', () => list([fixtures.auditEvent])),
  http.get('*/api/v1/audit/export', () => new HttpResponse('[]', { status: 200, headers: { 'Content-Type': 'application/json' } })),

  http.get('*/api/v1/engagements/:id/reports', () => list(fixtures.reports)),
  http.post('*/api/v1/engagements/:id/reports', () => json(fixtures.reports[0], 201)),
  http.get('*/api/v1/reports/:id', () => json(fixtures.reports[0])),
  http.post('*/api/v1/reports/:id/approve', () => json({ ...fixtures.reports[0], status: 'FINAL_COMPLETE' })),
  http.post('*/api/v1/reports/:id/render', () => json({ ...fixtures.reports[0], pdf_key: 'reports/report-1.pdf' })),
  http.get('*/api/v1/reports/:id/preview', () => new HttpResponse('%PDF-1.4', { status: 200 })),
  http.get('*/api/v1/reports/:id/download', () => new HttpResponse('%PDF-1.4', { status: 200 })),

  http.get('*/api/v1/admin/model-profiles', () => list(fixtures.modelProfiles)),
  http.post('*/api/v1/admin/model-profiles', () => json(fixtures.modelProfiles[0], 201)),
  http.put('*/api/v1/admin/model-profiles/:id', () => json(fixtures.modelProfiles[0])),
  http.get('*/api/v1/admin/risk-policies', () => list(fixtures.riskPolicies)),
  http.post('*/api/v1/admin/risk-policies', () => json(fixtures.riskPolicies[0], 201)),
  http.post('*/api/v1/admin/risk-policies/:id/activate', () => json(fixtures.riskPolicies[0])),
  http.get('*/api/v1/admin/settings', () => list([{ id: 'setting-1', key: 'session.timeout', value: { minutes: 30 }, version: 1 }])),
  http.put('*/api/v1/admin/settings/:key', () => json({ key: 'session.timeout' })),
  http.get('*/api/v1/admin/health', () => json({ status: 'ok', checks: { database: true, audit: true, evidence_storage: true } })),

  http.get('*/api/v1/access/users', () => list(fixtures.users)),
  http.post('*/api/v1/access/users', () => json({ user: fixtures.users[1], temporary_password: 'temporary-pass' }, 201)),
  http.put('*/api/v1/access/users/:id/roles', () => json({ user: fixtures.users[1] })),
  http.put('*/api/v1/access/users/:id/disabled', () => json({ user: { ...fixtures.users[1], disabled: true } })),
  http.post('*/api/v1/access/users/:id/reset-mfa', () => json({ user: { ...fixtures.users[1], totp_enabled: false } })),
  http.post('*/api/v1/access/users/:id/reset-password', () => json({ temporary_password: 'new-temporary-password' }))
];

