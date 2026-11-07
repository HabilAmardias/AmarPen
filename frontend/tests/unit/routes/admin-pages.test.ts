import { render, screen, waitFor } from '@testing-library/svelte';
import { HttpResponse, http } from 'msw';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';
import AdminLayout from '../../../src/routes/(app)/admin/+layout.svelte';
import UsersPage from '../../../src/routes/(app)/admin/users/+page.svelte';
import PromptsPage from '../../../src/routes/(app)/admin/prompts/+page.svelte';
import ModelProfilesPage from '../../../src/routes/(app)/admin/model-profiles/+page.svelte';
import RiskPoliciesPage from '../../../src/routes/(app)/admin/risk-policies/+page.svelte';
import McpRegistryPage from '../../../src/routes/(app)/admin/mcp/+page.svelte';
import { modelProfiles } from '../../mocks/fixtures';
import { server } from '../../setup';

describe('admin layout', () => {
  it('renders administration navigation', () => {
    render(AdminLayout);
    expect(screen.getByRole('link', { name: 'Users' })).toHaveAttribute('href', '/admin/users');
    expect(screen.getByRole('link', { name: 'System prompts' })).toHaveAttribute('href', '/admin/prompts');
  });
});

describe('admin users', () => {
  it('lists users and provisions an account', async () => {
    const user = userEvent.setup();
    render(UsersPage);
    await waitFor(() => expect(screen.getByText('analyst')).toBeInTheDocument());
    await user.type(screen.getByLabelText('Username'), 'newanalyst');
    await user.click(screen.getByRole('button', { name: 'Create account' }));
    await waitFor(() => expect(screen.getByText(/Temporary password:/)).toBeInTheDocument());
  });

  it('supports administrator MFA and password recovery', async () => {
    const user = userEvent.setup();
    render(UsersPage);
    await waitFor(() => expect(screen.getByText('analyst')).toBeInTheDocument());
    await user.click(screen.getAllByRole('button', { name: 'Reset MFA' })[0]);
    await waitFor(() => expect(screen.getByText('analyst')).toBeInTheDocument());
    await user.click(screen.getAllByRole('button', { name: 'Reset password' })[0]);
    await waitFor(() => expect(screen.getByText('new-temporary-password')).toBeInTheDocument());
  });
});

describe('admin prompts', () => {
  it('shows bodies, release state, and validation controls', async () => {
    render(PromptsPage);
    await waitFor(() => expect(screen.getByText('agent-orchestrator')).toBeInTheDocument());
    expect(screen.getByText(/Act safely within scope/)).toBeInTheDocument();
    expect(screen.getByText('baseline-1')).toBeInTheDocument();
    expect(screen.getAllByRole('button', { name: 'Validate' }).length).toBeGreaterThan(0);
  });
});

describe('admin model profiles', () => {
  it('lists profiles, health, and connection test controls', async () => {
    const user = userEvent.setup();
    render(ModelProfilesPage);
    await waitFor(() => expect(screen.getByText('local-default')).toBeInTheDocument());
    expect(screen.getByText(/Platform health:/)).toBeInTheDocument();
    expect(screen.getByText('REACHABLE')).toBeInTheDocument();
    expect(screen.getByText('Agent-ready')).toBeInTheDocument();
    expect(screen.getByText('Declared capabilities')).toBeInTheDocument();
    expect(screen.getByLabelText('Structured outputs')).toBeChecked();
    await user.click(screen.getByRole('button', { name: 'Test connection' }));
    await waitFor(() => expect(screen.getByText(/Connection test:/)).toBeInTheDocument());
  });

  it('requires and sends an API key for approved cloud profiles', async () => {
    const user = userEvent.setup();
    let payload: Record<string, unknown> = {};
    server.use(
      http.post('*/api/v1/admin/model-profiles', async ({ request }) => {
        payload = (await request.json()) as Record<string, unknown>;
        return HttpResponse.json(
          { ...modelProfiles[0], has_api_key: true, credential_source: 'stored' },
          { status: 201 }
        );
      })
    );
    render(ModelProfilesPage);
    await waitFor(() => expect(screen.getByText('local-default')).toBeInTheDocument());
    await user.type(screen.getByLabelText('Name'), 'cloud-profile');
    await user.selectOptions(screen.getByLabelText('Data boundary'), 'approved_cloud');
    const keyInput = screen.getByLabelText('API key');
    expect(keyInput).toBeRequired();
    await user.type(keyInput, 'sk-cloud-secret');
    await user.click(screen.getByRole('button', { name: 'Create profile' }));
    await waitFor(() => expect(screen.getByText(/Profile created/)).toBeInTheDocument());
    expect(payload.api_key).toBe('sk-cloud-secret');
    expect(screen.queryByDisplayValue('sk-cloud-secret')).not.toBeInTheDocument();
  });

  it('updates an existing API key without prefilling it', async () => {
    const user = userEvent.setup();
    render(ModelProfilesPage);
    await waitFor(() => expect(screen.getByText('local-default')).toBeInTheDocument());
    await user.click(screen.getByRole('button', { name: 'Add key' }));
    const input = screen.getByLabelText('New API key for local-default');
    expect(input).toHaveValue('');
    await user.type(input, 'sk-replacement');
    await user.click(screen.getByRole('button', { name: 'Save API key' }));
    await waitFor(() => expect(screen.getByText(/API key updated/)).toBeInTheDocument());
    expect(screen.queryByDisplayValue('sk-replacement')).not.toBeInTheDocument();
  });
});

describe('admin MCP registry', () => {
  it('shows server readiness and manifest controls', async () => {
    render(McpRegistryPage);
    await waitFor(() => expect(screen.getByText('local-mcp')).toBeInTheDocument());
    expect(screen.getByText(/MCP READINESS/)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Refresh discovery' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Activate' })).toBeInTheDocument();
  });

  it('registers a server and validates a discovered manifest', async () => {
    const user = userEvent.setup();
    vi.spyOn(window, 'confirm').mockReturnValue(true);
    render(McpRegistryPage);
    await waitFor(() => expect(screen.getByText('local-mcp')).toBeInTheDocument());
    await user.type(screen.getByLabelText('Stable ID'), 'new-mcp');
    await user.type(screen.getByLabelText('Endpoint'), 'https://mcp-server:8443/mcp');
    await user.click(screen.getByRole('button', { name: 'Register server' }));
    await waitFor(() => expect(screen.getByText(/MCP server registered/)).toBeInTheDocument());
    await waitFor(() => expect(screen.getByText('local-mcp')).toBeInTheDocument());
    await user.click(screen.getAllByRole('button', { name: 'Validate' })[0]);
    await waitFor(() => expect(screen.getByText('Manifest validation recorded.')).toBeInTheDocument());
    await waitFor(() => expect(screen.getByText('local-mcp')).toBeInTheDocument());
    await user.click(screen.getByRole('button', { name: 'Revoke server' }));
    await waitFor(() => expect(screen.getByText(/MCP server revoked/)).toBeInTheDocument());
  });
});

describe('admin risk policies', () => {
  it('lists policies and supports creating a version', async () => {
    const user = userEvent.setup();
    render(RiskPoliciesPage);
    await waitFor(() => expect(screen.getByText('Initial proposed matrix')).toBeInTheDocument());
    await user.type(screen.getByLabelText('Policy name'), 'Approved matrix');
    await user.click(screen.getByRole('button', { name: 'Create version' }));
    await waitFor(() => expect(screen.getByText('Initial proposed matrix')).toBeInTheDocument());
  });
});
