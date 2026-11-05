import { render, screen, waitFor } from '@testing-library/svelte';
import userEvent from '@testing-library/user-event';
import { describe, expect, it } from 'vitest';
import AdminLayout from '../../../src/routes/(app)/admin/+layout.svelte';
import UsersPage from '../../../src/routes/(app)/admin/users/+page.svelte';
import PromptsPage from '../../../src/routes/(app)/admin/prompts/+page.svelte';
import ModelProfilesPage from '../../../src/routes/(app)/admin/model-profiles/+page.svelte';
import RiskPoliciesPage from '../../../src/routes/(app)/admin/risk-policies/+page.svelte';

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
  it('lists profiles and platform health', async () => {
    render(ModelProfilesPage);
    await waitFor(() => expect(screen.getByText('local-default')).toBeInTheDocument());
    expect(screen.getByText(/Platform health:/)).toBeInTheDocument();
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
