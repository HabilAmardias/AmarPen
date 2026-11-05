import { render, screen } from '@testing-library/svelte';
import { describe, expect, it } from 'vitest';
import CoverageTable from '../../../src/lib/components/CoverageTable.svelte';
import SeverityMeter from '../../../src/lib/components/SeverityMeter.svelte';
import { assessment, coverage } from '../../mocks/fixtures';

describe('SeverityMeter', () => {
  it('keeps calculated, manual, and business risk distinct', () => {
    render(SeverityMeter, { props: { assessment } });
    expect(screen.getByText('9.9')).toBeInTheDocument();
    expect(screen.getAllByText('High').length).toBeGreaterThan(0);
    expect(screen.getByText('Compensating control present')).toBeInTheDocument();
    expect(screen.getByText('L4 × I4')).toBeInTheDocument();
  });
});

describe('CoverageTable', () => {
  it('shows coverage outcomes and reasons', () => {
    render(CoverageTable, { props: { records: coverage.records } });
    expect(screen.getByText('WSTG-INFO-01')).toBeInTheDocument();
    expect(screen.getByText('Tool failed')).toBeInTheDocument();
  });

  it('shows an empty state', () => {
    render(CoverageTable, { props: { records: [] } });
    expect(screen.getByText('No coverage records')).toBeInTheDocument();
  });
});
