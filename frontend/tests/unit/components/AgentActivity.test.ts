import { render, screen } from '@testing-library/svelte';
import { describe, expect, it } from 'vitest';
import AgentActivity from '../../../src/lib/components/AgentActivity.svelte';

const activity = {
  tasks: [
    { id: 'task-1', run_id: 'run-1', role: 'orchestrator', kind: 'orchestrate', state: 'COMPLETED', asset: 'example.com', attempt: 1, outcome: 'SUCCEEDED', ownership_key: 'orchestrator:initial:example.com', result_id: 'result-1' },
    { id: 'task-2', run_id: 'run-1', role: 'validation', kind: 'validation', state: 'RUNNING', asset: 'example.com', attempt: 1, outcome: '', ownership_key: 'validation:finding-1:1', result_id: '' }
  ],
  results: [
    { id: 'result-1', task_id: 'task-1', role: 'orchestrator', status: 'SUCCEEDED', limitations: ['No authenticated workflow context'], stale: false }
  ],
  proposals: [
    { id: 'proposal-1', task_id: 'task-1', kind: 'schedule_task', status: 'APPROVED', decision_reason: '' }
  ],
  assets: [{ id: 'asset-1', kind: 'target', value: 'example.com' }]
};

describe('AgentActivity', () => {
  it('shows role, state, outcome, and limitations', () => {
    render(AgentActivity, { props: { activity } });
    expect(screen.getByText('orchestrator')).toBeInTheDocument();
    expect(screen.getByText('validation')).toBeInTheDocument();
    expect(screen.getByText('No authenticated workflow context')).toBeInTheDocument();
    expect(screen.getByText('target: example.com')).toBeInTheDocument();
  });

  it('shows an empty state', () => {
    render(AgentActivity, { props: { activity: { tasks: [], results: [], proposals: [], assets: [] } } });
    expect(screen.getByText('No agent tasks')).toBeInTheDocument();
  });
});
