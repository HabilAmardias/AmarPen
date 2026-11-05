import { fireEvent, render, screen } from '@testing-library/svelte';
import { describe, expect, it, vi } from 'vitest';
import EmptyState from '../../../src/lib/components/EmptyState.svelte';
import ErrorView from '../../../src/lib/components/ErrorView.svelte';
import LoadingState from '../../../src/lib/components/LoadingState.svelte';

describe('LoadingState', () => {
  it('announces progress', () => {
    render(LoadingState, { props: { label: 'Loading findings' } });
    expect(screen.getByRole('status')).toHaveTextContent('Loading findings');
  });
});

describe('EmptyState', () => {
  it('renders title and message', () => {
    render(EmptyState, { props: { title: 'Nothing yet', message: 'Create one first.' } });
    expect(screen.getByText('Nothing yet')).toBeInTheDocument();
    expect(screen.getByText('Create one first.')).toBeInTheDocument();
  });
});

describe('ErrorView', () => {
  it('shows correlation and invokes retry', async () => {
    const onretry = vi.fn();
    render(ErrorView, {
      props: { title: 'Failed', message: 'Try again', correlationId: 'corr-1', onretry }
    });
    expect(screen.getByText('CORRELATION')).toBeInTheDocument();
    expect(screen.getByText('corr-1')).toBeInTheDocument();
    await fireEvent.click(screen.getByRole('button', { name: 'Try again' }));
    expect(onretry).toHaveBeenCalled();
  });
});
