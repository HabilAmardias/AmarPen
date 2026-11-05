import { fireEvent, render, screen, waitFor } from '@testing-library/svelte';
import userEvent from '@testing-library/user-event';
import { goto } from '$app/navigation';
import { describe, expect, it } from 'vitest';
import RootPage from '../../../src/routes/+page.svelte';
import ErrorPage from '../../../src/routes/+error.svelte';
import LoginPage from '../../../src/routes/login/+page.svelte';
import TotpPage from '../../../src/routes/login/totp/+page.svelte';
import EnrollPage from '../../../src/routes/account/enroll/+page.svelte';
import RecoveryPage from '../../../src/routes/account/recovery/+page.svelte';

describe('root and error pages', () => {
  it('root page routes an authenticated session to the dashboard', async () => {
    render(RootPage);
    await waitFor(() => expect(goto).toHaveBeenCalledWith('/dashboard'));
  });

  it('error page explains the failure and offers recovery', () => {
    render(ErrorPage);
    expect(screen.getByRole('heading', { name: 'Page unavailable' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Return to dashboard' })).toHaveAttribute('href', '/dashboard');
  });
});

describe('login pages', () => {
  it('submits credentials and routes to the TOTP step', async () => {
    const user = userEvent.setup();
    render(LoginPage);
    await user.type(screen.getByLabelText('Username'), 'admin');
    await user.type(screen.getByLabelText('Password'), 'correct horse battery');
    await user.click(screen.getByRole('button', { name: 'Continue' }));
    await waitFor(() => expect(goto).toHaveBeenCalledWith('/login/totp'));
  });

  it('renders the six-digit pattern and normalizes formatted codes', async () => {
    render(TotpPage);
    const input = screen.getByLabelText('Authenticator code');
    expect(input).toHaveAttribute('pattern', '[0-9]{6}');
    await fireEvent.input(input, { target: { value: '123 456' } });
    expect(input).toHaveValue('123456');
    await fireEvent.submit(input.closest('form') as HTMLFormElement);
    await waitFor(() => expect(goto).toHaveBeenCalledWith('/dashboard'));
  });
});

describe('account pages', () => {
  it('loads the enrollment secret and verifies the code', async () => {
    render(EnrollPage);
    await waitFor(() => expect(screen.getByText('JBSWY3DPEHPK3PXP')).toBeInTheDocument());
    const input = screen.getByLabelText('Verification code');
    expect(input).toHaveAttribute('pattern', '[0-9]{6}');
    await fireEvent.input(input, { target: { value: '12-34-56' } });
    expect(input).toHaveValue('123456');
    await fireEvent.submit(input.closest('form') as HTMLFormElement);
    await waitFor(() => expect(screen.getByText('alpha-code')).toBeInTheDocument());
  });

  it('submits recovery details and reports success', async () => {
    const user = userEvent.setup();
    render(RecoveryPage);
    await user.type(screen.getByLabelText('Username'), 'admin');
    await user.type(screen.getByLabelText('Recovery code'), 'alpha-code');
    await user.type(screen.getByLabelText('New password'), 'correct horse battery');
    await user.click(screen.getByRole('button', { name: 'Recover account' }));
    await waitFor(() => expect(screen.getByText(/Recovery completed/)).toBeInTheDocument());
  });
});
