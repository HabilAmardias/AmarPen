import { http, HttpResponse } from 'msw';
import { describe, expect, it } from 'vitest';
import { api, ApiError } from '../../../src/lib/api/client';
import { server } from '../../setup';

describe('API client', () => {
  it('loads the current session with cookies included', async () => {
    const result = await api.auth.session();
    expect(result.user.username).toBe('admin');
    expect(result.csrf_token).toBe('csrf-token');
  });

  it('sends the CSRF header on mutations', async () => {
    let captured = '';
    document.cookie = 'pt_csrf=csrf-cookie; path=/';
    server.use(
      http.post('*/api/v1/auth/logout', ({ request }) => {
        captured = request.headers.get('X-CSRF-Token') ?? '';
        return new HttpResponse(null, { status: 204 });
      })
    );
    await api.auth.logout();
    expect(captured).toBe('csrf-cookie');
  });

  it('normalizes API errors', async () => {
    server.use(
      http.get('*/api/v1/engagements', () =>
        HttpResponse.json(
          { error: { code: 'conflict', message: 'Stale version', correlation_id: 'corr-1', details: {} } },
          { status: 409 }
        )
      )
    );
    await expect(api.engagements.list()).rejects.toMatchObject({
      name: 'ApiError',
      status: 409,
      code: 'conflict',
      correlationId: 'corr-1'
    });
  });

  it('builds evidence and report URLs', () => {
    expect(api.findings.evidenceUrl('evidence-1')).toContain('/api/v1/evidence/evidence-1');
    expect(api.reports.downloadUrl('report-1')).toContain('/api/v1/reports/report-1/download');
    expect(api.audit.exportUrl('csv')).toContain('format=csv');
  });

  it('exposes ApiError metadata', () => {
    const error = new ApiError(403, { error: { code: 'forbidden', message: 'Denied', details: {}, correlation_id: 'c' } });
    expect(error.message).toBe('Denied');
    expect(error.status).toBe(403);
  });
});
