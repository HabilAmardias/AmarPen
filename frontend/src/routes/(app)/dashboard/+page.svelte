<script lang="ts">
  import { onMount } from 'svelte';
  import { CaretRight, Plus, Pulse, ShieldCheck, Target } from 'phosphor-svelte';
  import { api, ApiError } from '../../../lib/api/client';
  import type { Engagement } from '../../../lib/api/types';
  import EmptyState from '../../../lib/components/EmptyState.svelte';
  import ErrorView from '../../../lib/components/ErrorView.svelte';
  import LoadingState from '../../../lib/components/LoadingState.svelte';
  import StatusBadge from '../../../lib/components/StatusBadge.svelte';

  let engagements: Engagement[] = [];
  let loading = true;
  let error = '';
  let correlationId = '';

  $: active = engagements.filter((engagement) => ['ACTIVE', 'READY'].includes(engagement.status)).length;
  $: authorized = engagements.filter((engagement) => engagement.authorization_valid).length;
  $: targets = engagements.reduce((total, engagement) => total + engagement.targets.length, 0);

  async function load() {
    loading = true;
    error = '';
    try {
      engagements = (await api.engagements.list()).items;
    } catch (cause) {
      error = cause instanceof ApiError ? cause.message : 'Unable to load engagements';
      correlationId = cause instanceof ApiError ? cause.correlationId : '';
    } finally {
      loading = false;
    }
  }

  onMount(load);
</script>

<svelte:head><title>Mission Control | AI-Assisted Pentest</title></svelte:head>

<div class="stack">
  <div class="operation-header">
    <div>
      <span class="panel-kicker">MISSION CONTROL</span>
      <h1>Engagements</h1>
      <p class="muted">Authorized assessments, readiness state, and execution controls.</p>
    </div>
    <a class="button" href="/engagements/new"><Plus size={15} weight="bold" aria-hidden="true" /> New engagement</a>
  </div>

  <div class="grid four">
    <div class="card stat-card">
      <span class="label"><Pulse size={13} aria-hidden="true" /> TOTAL OPERATIONS</span>
      <span class="value">{engagements.length}</span>
    </div>
    <div class="card stat-card">
      <span class="label"><ShieldCheck size={13} aria-hidden="true" /> ACTIVE / READY</span>
      <span class="value">{active}</span>
    </div>
    <div class="card stat-card">
      <span class="label"><Target size={13} aria-hidden="true" /> TARGET SURFACE</span>
      <span class="value">{targets}</span>
    </div>
    <div class="card stat-card">
      <span class="label"><ShieldCheck size={13} aria-hidden="true" /> AUTHORIZED</span>
      <span class="value">{authorized}</span>
    </div>
  </div>

  {#if loading}
    <LoadingState label="Loading engagements" />
  {:else if error}
    <ErrorView title="Could not load engagements" message={error} {correlationId} onretry={load} />
  {:else if engagements.length === 0}
    <EmptyState title="No engagements yet" message="Create an engagement to record authorization, scope, and business context.">
      <a class="button" href="/engagements/new">Create engagement</a>
    </EmptyState>
  {:else}
    <div class="card">
      <div class="row" style="justify-content: space-between; margin-bottom: 0.7rem;">
        <span class="panel-kicker">OPERATION REGISTER</span>
        <span class="hud-meta"><span>{engagements.length} RECORDS</span><span>LOCAL STORE</span></span>
      </div>
      <table>
        <caption class="sr-only">Engagement list</caption>
        <thead>
          <tr>
            <th scope="col">Operation</th>
            <th scope="col">State</th>
            <th scope="col">Targets</th>
            <th scope="col">Authorization</th>
            <th scope="col">Last Update</th>
            <th scope="col"><span class="sr-only">Open</span></th>
          </tr>
        </thead>
        <tbody>
          {#each engagements as engagement (engagement.id)}
            <tr>
              <td>
                <a class="operation-name" href={`/engagements/${engagement.id}`}>{engagement.name}</a>
                <div class="small muted">{engagement.description || 'External black-box assessment'}</div>
              </td>
              <td><StatusBadge value={engagement.status} /></td>
              <td>
                <ul class="target-list">
                  {#each engagement.targets.slice(0, 3) as target}
                    <li class="chip">{target}</li>
                  {/each}
                  {#if engagement.targets.length > 3}<li class="chip">+{engagement.targets.length - 3}</li>{/if}
                </ul>
              </td>
              <td>
                <span class="auth-mark" class:valid={engagement.authorization_valid}>
                  {engagement.authorization_valid ? 'RECORDED' : 'MISSING'}
                </span>
              </td>
              <td class="muted">{new Date(engagement.updated_at).toLocaleString()}</td>
              <td><a class="open-link" href={`/engagements/${engagement.id}`} aria-label={`Open ${engagement.name}`}><CaretRight size={15} aria-hidden="true" /></a></td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  {/if}
</div>

<style>
  .stat-card .label {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
  }

  .operation-name {
    font-weight: 500;
    text-decoration: none;
  }

  .operation-name:hover {
    color: var(--primary);
    text-shadow: 0 0 12px rgba(57, 255, 136, 0.2);
  }

  .auth-mark {
    color: var(--danger);
    font-size: 0.64rem;
    letter-spacing: 0.1em;
  }

  .auth-mark.valid {
    color: var(--primary);
  }

  .open-link {
    display: inline-flex;
    color: var(--text-dim);
    text-decoration: none;
  }

  .open-link:hover {
    color: var(--primary);
  }

  @media (max-width: 760px) {
    .operation-header {
      align-items: stretch;
    }

    .operation-header .button {
      width: 100%;
    }
  }
</style>
