import { render, screen } from '@testing-library/svelte';
import { describe, expect, it } from 'vitest';
import StatusBadge from '../../../src/lib/components/StatusBadge.svelte';

describe('StatusBadge', () => {
  it('renders a human label and semantic tone', () => {
    render(StatusBadge, { props: { value: 'COMPLETED' } });
    const badge = screen.getByTestId('status-badge');
    expect(badge).toHaveTextContent('COMPLETED');
    expect(badge).toHaveClass('success');
  });

  it('uses a provided label', () => {
    render(StatusBadge, { props: { value: 'PAUSING', label: 'Pausing' } });
    expect(screen.getByText('Pausing')).toBeInTheDocument();
  });
});
