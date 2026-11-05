import { fireEvent, render, screen } from '@testing-library/svelte';
import { describe, expect, it, vi } from 'vitest';
import ConfirmDialog from '../../../src/lib/components/ConfirmDialog.svelte';

describe('ConfirmDialog', () => {
  it('does not render when closed', () => {
    render(ConfirmDialog, { props: { open: false } });
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  });

  it('confirms and cancels', async () => {
    const onconfirm = vi.fn();
    const oncancel = vi.fn();
    render(ConfirmDialog, {
      props: { open: true, title: 'Stop run?', message: 'Permanent.', onconfirm, oncancel }
    });
    expect(screen.getByRole('dialog')).toHaveAccessibleName('Stop run?');
    await fireEvent.click(screen.getByRole('button', { name: 'Confirm' }));
    expect(onconfirm).toHaveBeenCalled();
    await fireEvent.click(screen.getByRole('button', { name: 'Cancel' }));
    expect(oncancel).toHaveBeenCalled();
  });
});
