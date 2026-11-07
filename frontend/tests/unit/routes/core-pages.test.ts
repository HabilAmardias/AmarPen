import { render, screen, waitFor } from '@testing-library/svelte';
import userEvent from '@testing-library/user-event';
import { goto } from '$app/navigation';
import { describe, expect, it, vi } from 'vitest';
import { HttpResponse, http } from 'msw';
import AppLayout from '../../../src/routes/(app)/+layout.svelte';
import DashboardPage from '../../../src/routes/(app)/dashboard/+page.svelte';
import NewEngagementPage from '../../../src/routes/(app)/engagements/new/+page.svelte';
import EngagementPage from '../../../src/routes/(app)/engagements/[id]/+page.svelte';
import EditEngagementPage from '../../../src/routes/(app)/engagements/[id]/edit/+page.svelte';
import CoveragePage from '../../../src/routes/(app)/engagements/[id]/coverage/+page.svelte';
import FindingsPage from '../../../src/routes/(app)/engagements/[id]/findings/+page.svelte';
import FindingPage from '../../../src/routes/(app)/engagements/[id]/findings/[findingId]/+page.svelte';
import ReportsPage from '../../../src/routes/(app)/engagements/[id]/reports/+page.svelte';
import AuditPage from '../../../src/routes/(app)/audit/+page.svelte';
import { run } from '../../mocks/fixtures';
import { server } from '../../setup';

describe('authenticated layout', () => {
  it('loads the session and renders the shell', async () => {
    render(AppLayout);
    await waitFor(() => expect(screen.getByText('admin')).toBeInTheDocument());
    expect(screen.getByRole('link', { name: 'Administration' })).toHaveAttribute('href', '/admin/users');
  });
});

describe('engagement pages', () => {
  it('dashboard lists engagements', async () => {
    render(DashboardPage);
    await waitFor(() => expect(screen.getByText('Acme external assessment')).toBeInTheDocument());
    expect(screen.getByRole('link', { name: 'New engagement' })).toHaveAttribute('href', '/engagements/new');
  });

  it('creates an attested engagement from a base URL', async () => {
    const user = userEvent.setup();
    render(NewEngagementPage);
    await user.type(screen.getByLabelText('Base URL'), 'https://example.org');
    await user.click(screen.getByRole('checkbox'));
    expect(screen.getByText(/I confirm I own this target/)).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: 'Authorize and create' }));
    await waitFor(() => expect(goto).toHaveBeenCalledWith('/engagements/eng-1'));
  });

  it('engagement detail shows readiness and run controls', async () => {
    render(EngagementPage, { props: { data: { id: 'eng-1' } } });
    await waitFor(() => expect(screen.getByRole('heading', { name: 'Acme external assessment' })).toBeInTheDocument());
    expect(screen.getByRole('heading', { name: 'Readiness' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Pause' })).toBeInTheDocument();
    expect(screen.getByText('WSTG-BUSL-01')).toBeInTheDocument();
  });

  it('refreshes background run state without reloading the page', async () => {
    const polls: Array<() => void> = [];
    vi.spyOn(globalThis, 'setInterval').mockImplementation(((handler: () => void) => {
      polls.push(handler);
      return 1 as unknown as ReturnType<typeof setInterval>;
    }) as typeof setInterval);
    server.use(
      http.get('*/api/v1/runs/run-1', () => HttpResponse.json({ ...run, state: 'COMPLETED' }))
    );
    render(EngagementPage, { props: { data: { id: 'eng-1' } } });
    await waitFor(() => expect(screen.getByText(/Execution is managed server-side/)).toBeInTheDocument());
    await waitFor(() => expect(polls.length).toBeGreaterThan(0));
    await Promise.all(polls.map((poll) => Promise.resolve(poll())));
    await waitFor(() => expect(screen.queryByText(/Execution is managed server-side/)).not.toBeInTheDocument());
    expect(screen.getAllByText('COMPLETED').length).toBeGreaterThan(0);
  });

  it('edit engagement prefills authorization and uses the model dropdown', async () => {
    const user = userEvent.setup();
    render(EditEngagementPage, { props: { data: { id: 'eng-1' } } });
    await waitFor(() => expect(screen.getByLabelText('Authorization reference')).toHaveValue('AUTH-2026-01'));
    const model = screen.getByLabelText('Model profile') as HTMLSelectElement;
    expect(model.value).toBe('local-default');
    expect(model.tagName).toBe('SELECT');
    await user.click(screen.getByLabelText(/Authorization is recorded and valid/));
    await user.click(screen.getByRole('button', { name: 'Save changes' }));
    await waitFor(() => expect(goto).toHaveBeenCalledWith('/engagements/eng-1'));
  });

  it('coverage page shows counts and records', async () => {
    render(CoveragePage, { props: { data: { id: 'eng-1' } } });
    await waitFor(() => expect(screen.getByText('WSTG-INFO-01')).toBeInTheDocument());
    expect(screen.getByText('TESTED NO ISSUE OBSERVED')).toBeInTheDocument();
  });
});

describe('finding pages', () => {
  it('findings list displays candidates and validation context', async () => {
    render(FindingsPage, { props: { data: { id: 'eng-1' } } });
    await waitFor(() => expect(screen.getByRole('link', { name: 'Reflected cross-site scripting' })).toBeInTheDocument());
    expect(screen.getByText(/Candidates require evidence/)).toBeInTheDocument();
  });

  it('finding detail separates calculated, manual, and business risk', async () => {
    render(FindingPage, { props: { data: { id: 'eng-1', findingId: 'finding-1' } } });
    await waitFor(() => expect(screen.getByRole('heading', { name: 'Reflected cross-site scripting' })).toBeInTheDocument());
    expect(screen.getByText('Calculated CVSS')).toBeInTheDocument();
    expect(screen.getAllByText('Manual reported severity').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Business risk').length).toBeGreaterThan(0);
    expect(screen.getByRole('link', { name: 'request_response' })).toBeInTheDocument();
  });

  it('finding detail creates a selected-finding retest', async () => {
    const user = userEvent.setup();
    render(FindingPage, { props: { data: { id: 'eng-1', findingId: 'finding-1' } } });
    await waitFor(() => expect(screen.getByRole('button', { name: 'Start selected-finding retest' })).toBeInTheDocument());
    await user.click(screen.getByRole('button', { name: 'Start selected-finding retest' }));
    await waitFor(() => expect(screen.getByText('Retest run created.')).toBeInTheDocument());
  });
});

describe('report and audit pages', () => {
  it('reports page supports approval and rendering', async () => {
    const user = userEvent.setup();
    render(ReportsPage, { props: { data: { id: 'eng-1' } } });
    await waitFor(() => expect(screen.getByText('v1')).toBeInTheDocument());
    await user.click(screen.getByRole('button', { name: 'Approve' }));
    await waitFor(() => expect(screen.getByText('Report approved.')).toBeInTheDocument());
    await user.click(screen.getByRole('button', { name: 'Render' }));
    await waitFor(() => expect(screen.getByText('PDF rendered from snapshot.')).toBeInTheDocument());
  });

  it('audit page filters and displays events', async () => {
    render(AuditPage);
    await waitFor(() => expect(screen.getByText('engagement.created')).toBeInTheDocument());
    expect(screen.getByRole('link', { name: 'Export JSON' })).toBeInTheDocument();
  });
});
