<script lang="ts">
  import { Pause, Play, Stop } from 'phosphor-svelte';
  import { api, ApiError } from '../api/client';
  import type { Run } from '../api/types';
  import ConfirmDialog from './ConfirmDialog.svelte';
  import StatusBadge from './StatusBadge.svelte';

  export let run: Run | null = null;
  export let onchange: (run: Run) => void = () => {};

  let pending = '';
  let error = '';
  let showStop = false;

  $: state = run?.state ?? 'NOT_STARTED';
  $: paused = state === 'PAUSED';
  $: active = ['QUEUED', 'RUNNING', 'PAUSING', 'PAUSED', 'STOPPING'].includes(state);
  $: transitional = ['PAUSING', 'STOPPING'].includes(state);
  $: finished = ['COMPLETED', 'STOPPED', 'FAILED'].includes(state);
  const states = ['QUEUED', 'RUNNING', 'PAUSING', 'PAUSED', 'STOPPING', 'STOPPED', 'COMPLETED', 'FAILED'];

  function key(action: string): string {
    return `${action}-${run?.id ?? 'new'}-${Date.now()}-${Math.random().toString(16).slice(2)}`;
  }

  async function act(action: 'pause' | 'resume' | 'stop') {
    if (!run) return;
    pending = action;
    error = '';
    try {
      const updated =
        action === 'pause'
          ? await api.runs.pause(run.id, key('pause'))
          : action === 'resume'
            ? await api.runs.resume(run.id, key('resume'))
            : await api.runs.stop(run.id, key('stop'), 'Stopped from live run controls');
      onchange(updated);
    } catch (cause) {
      error = cause instanceof ApiError ? cause.message : 'Run control request failed';
    } finally {
      pending = '';
      showStop = false;
    }
  }
</script>

<div class="run-controls">
  <div class="control-head">
    <div class="control-state">
      <span class="state-label">EXECUTION STATE</span>
      <StatusBadge value={state} />
    </div>
    {#if transitional}
      <span class="awaiting"><span class="status-orb" aria-hidden="true"></span> Waiting for worker confirmation…</span>
    {:else if finished}
      <span class="terminal-state">TERMINAL STATE / RUN CLOSED</span>
    {:else}
      <span class="terminal-state">CONTROL CHANNEL / LIVE</span>
    {/if}
  </div>

  <div class="state-track" aria-label="Run state sequence">
    {#each states as item}
      <span class:current={item === state} class:past={states.indexOf(item) < states.indexOf(state)}>{item}</span>
    {/each}
  </div>

  <div class="control-actions">
    <button
      type="button"
      class="secondary"
      disabled={!active || paused || transitional || pending !== ''}
      on:click={() => act('pause')}
    >
      <Pause size={14} weight="bold" aria-hidden="true" />
      {pending === 'pause' || state === 'PAUSING' ? 'Pausing…' : 'Pause'}
    </button>
    <button type="button" class="secondary" disabled={!paused || pending !== ''} on:click={() => act('resume')}>
      <Play size={14} weight="bold" aria-hidden="true" />
      {pending === 'resume' ? 'Resuming…' : 'Resume'}
    </button>
    <button type="button" class="danger" disabled={!active || finished || pending !== ''} on:click={() => (showStop = true)}>
      <Stop size={14} weight="bold" aria-hidden="true" />
      {pending === 'stop' || state === 'STOPPING' ? 'Stopping…' : 'Stop run'}
    </button>
  </div>

  {#if error}<div class="alert error" role="alert">{error}</div>{/if}
</div>

<ConfirmDialog
  open={showStop}
  title="Stop this run?"
  message="Stopping is permanent for this run. Collected evidence is retained, but the run cannot resume. A linked new run is required to continue."
  confirmLabel="Stop run"
  danger={true}
  onconfirm={() => act('stop')}
  oncancel={() => (showStop = false)}
/>

<style>
  .run-controls {
    display: grid;
    gap: 0.8rem;
  }

  .control-head {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 0.6rem;
    flex-wrap: wrap;
  }

  .control-state {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .state-label,
  .terminal-state {
    color: var(--text-dim);
    font-size: 0.58rem;
    letter-spacing: 0.14em;
  }

  .awaiting {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    color: var(--amber);
    font-size: 0.7rem;
  }

  .awaiting .status-orb {
    background: var(--amber);
    color: var(--amber);
    box-shadow: 0 0 10px var(--amber);
  }

  .state-track {
    display: flex;
    gap: 0.18rem;
    flex-wrap: wrap;
    padding: 0.42rem;
    border: 1px solid var(--border);
    background: var(--surface-inset);
  }

  .state-track span {
    flex: 1;
    min-width: 4.2rem;
    padding: 0.2rem 0.32rem;
    border: 1px solid transparent;
    color: var(--text-dim);
    font-size: 0.54rem;
    letter-spacing: 0.04em;
    text-align: center;
  }

  .state-track span.past {
    color: var(--text-muted);
    border-color: rgba(42, 74, 68, 0.4);
  }

  .state-track span.current {
    color: var(--primary);
    border-color: rgba(57, 255, 136, 0.4);
    background: rgba(57, 255, 136, 0.07);
    box-shadow: 0 0 12px rgba(57, 255, 136, 0.08);
  }

  .control-actions {
    display: flex;
    flex-wrap: wrap;
    gap: 0.45rem;
  }

  .control-actions button {
    flex: 1 1 8rem;
  }

  @media (max-width: 560px) {
    .state-track span {
      min-width: 3.4rem;
      font-size: 0.48rem;
    }
  }
</style>
