import { render, screen, waitFor, within } from '@testing-library/svelte';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';
import RunControls from '../../../src/lib/components/RunControls.svelte';
import { run } from '../../mocks/fixtures';

describe('RunControls', () => {
  it('shows PAUSING after a pause request and waits for confirmation', async () => {
    const user = userEvent.setup();
    const onchange = vi.fn();
    const view = render(RunControls, { props: { run: { ...run, state: 'RUNNING' }, onchange } });
    await user.click(screen.getByRole('button', { name: 'Pause' }));
    await waitFor(() => expect(onchange).toHaveBeenCalled());
    await view.rerender({ run: { ...run, state: 'PAUSING' }, onchange });
    expect(screen.getByText('Waiting for worker confirmation…')).toBeInTheDocument();
  });

  it('requires confirmation before stopping and explains irreversibility', async () => {
    const user = userEvent.setup();
    const onchange = vi.fn();
    render(RunControls, { props: { run: { ...run, state: 'RUNNING' }, onchange } });
    await user.click(screen.getByRole('button', { name: 'Stop run' }));
    const dialog = screen.getByRole('dialog');
    expect(dialog).toHaveTextContent('cannot resume');
    await user.click(within(dialog).getByRole('button', { name: 'Stop run' }));
    await waitFor(() => expect(onchange).toHaveBeenCalled());
  });
});
