<script lang="ts">
  import { onMount } from 'svelte';
  import { DownloadSimple, Fingerprint, ListMagnifyingGlass } from 'phosphor-svelte';
  import { api, ApiError } from '../../../lib/api/client';
  import type { AuditEvent } from '../../../lib/api/types';
  import EmptyState from '../../../lib/components/EmptyState.svelte';
  import ErrorView from '../../../lib/components/ErrorView.svelte';
  import LoadingState from '../../../lib/components/LoadingState.svelte';
  import StatusBadge from '../../../lib/components/StatusBadge.svelte';

  let events: AuditEvent[] = [];
  let action = '';
  let actorId = '';
  let outcome = '';
  let loading = true;
  let error = '';

  async function load() {
    loading = true;
    error = '';
    try {
      const params = new URLSearchParams();
      if (action) params.set('action', action);
      if (actorId) params.set('actor_id', actorId);
      if (outcome) params.set('outcome', outcome);
      events = (await api.audit.events(params.toString())).items;
    } catch (cause) {
      error = cause instanceof ApiError ? cause.message : 'Unable to load audit events';
    } finally {
      loading = false;
    }
  }

  onMount(load);
</script>

<svelte:head><title>Audit explorer | AI-Assisted Pentest</title></svelte:head>

<div class="stack">
  <div class="operation-header">
    <div>
      <span class="panel-kicker">AUDIT EXPLORER</span>
      <h1>Event Log</h1>
      <p class="muted">Actor, action, affected resource, outcome, and correlation are retained for accountability.</p>
    </div>
    <a class="button secondary" href={api.audit.exportUrl('json')}><DownloadSimple size={14} aria-hidden="true" /> Export JSON</a>
  </div>

  <form class="card filter-console" on:submit|preventDefault={load}>
    <div class="row" style="justify-content: space-between;">
      <span class="panel-kicker">QUERY CONSOLE</span>
      <ListMagnifyingGlass size={17} aria-hidden="true" class="text-cyan" />
    </div>
    <div class="grid three">
      <label>Action <input bind:value={action} placeholder="finding.validated" /></label>
      <label>
        Actor ID
        <span class="input-inline"><Fingerprint size={14} aria-hidden="true" /><input bind:value={actorId} placeholder="user-1" /></span>
      </label>
      <label>
        Outcome
        <select bind:value={outcome}>
          <option value="">Any</option>
          <option value="SUCCESS">Success</option>
          <option value="DENIED">Denied</option>
          <option value="FAILURE">Failure</option>
        </select>
      </label>
    </div>
    <button type="submit">Apply filters</button>
  </form>

  {#if loading}
    <LoadingState label="Loading audit events" />
  {:else if error}
    <ErrorView title="Could not load audit events" message={error} onretry={load} />
  {:else if events.length === 0}
    <EmptyState title="No matching audit events" message="Adjust the filters or verify that your role can read audit scope." />
  {:else}
    <div class="card">
      <div class="row" style="justify-content: space-between; margin-bottom: 0.5rem;">
        <span class="panel-kicker">CHRONOLOGICAL EVENTS</span>
        <span class="hud-meta"><span>{events.length} EVENTS</span><span>UTC</span></span>
      </div>
      <table>
        <caption class="sr-only">Audit events</caption>
        <thead><tr><th scope="col">Time</th><th scope="col">Actor</th><th scope="col">Action</th><th scope="col">Resource</th><th scope="col">Outcome</th></tr></thead>
        <tbody>
          {#each events as event (event.event_id)}
            <tr>
              <td class="muted timestamp">{new Date(event.occurred_at).toLocaleString()}</td>
              <td><span class="actor">{event.actor_type}: {event.actor_id}</span></td>
              <td class="action-cell">{event.action}</td>
              <td>{event.resource}{#if event.asset}<span class="small muted"> ({event.asset})</span>{/if}</td>
              <td><StatusBadge value={event.outcome} /></td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  {/if}
</div>

<style>
  .filter-console {
    display: grid;
    gap: 0.7rem;
  }

  .filter-console button {
    justify-self: start;
  }

  .input-inline {
    display: flex;
    align-items: center;
    gap: 0.4rem;
    padding-left: 0.55rem;
    border: 1px solid var(--border);
    background: var(--surface-inset);
    color: var(--text-dim);
  }

  .input-inline:focus-within {
    border-color: var(--primary);
    color: var(--primary);
  }

  .input-inline input {
    border: 0;
    background: transparent;
    box-shadow: none;
    padding-left: 0;
  }

  .timestamp,
  .actor,
  .action-cell {
    font-size: 0.72rem;
  }

  .action-cell {
    color: var(--cyan);
  }
</style>
