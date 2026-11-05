import { render, screen, waitFor } from '@testing-library/svelte';
import userEvent from '@testing-library/user-event';
import { goto } from '$app/navigation';
import { describe, expect, it, vi } from 'vitest';
import AppShell from '../../../src/lib/components/AppShell.svelte';

describe('AppShell', () => {
  it('renders navigation and the signed-in user', () => {
    render(AppShell, { props: { user: { username: 'admin', roles: ['Administrator'] } } });
    expect(screen.getByText('AI-Assisted Pentest')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Dashboard' })).toHaveAttribute('href', '/dashboard');
    expect(screen.getByText('admin')).toBeInTheDocument();
  });

  it('signs out and navigates to login', async () => {
    const user = userEvent.setup();
    render(AppShell, { props: { user: { username: 'admin', roles: ['Administrator'] } } });
    await user.click(screen.getByRole('button', { name: 'Sign out' }));
    await waitFor(() => expect(goto).toHaveBeenCalledWith('/login'));
    expect(vi.mocked(goto)).toHaveBeenCalled();
  });
});
