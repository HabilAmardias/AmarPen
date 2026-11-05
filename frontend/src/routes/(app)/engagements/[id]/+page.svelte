<script lang="ts">
  import { onMount } from 'svelte';
  import { Crosshair, Play, ShieldCheck, Target, WarningCircle } from 'phosphor-svelte';
  import { api, ApiError } from '../../../../lib/api/client';
  import type { AgentActivity as AgentActivityData, Engagement, Run, Scenario } from '../../../../lib/api/types';
  import AgentActivity from '../../../../lib/components/AgentActivity.svelte';
  import ErrorView from '../../../../lib/components/ErrorView.svelte';
  import LoadingState from '../../../../lib/components/LoadingState.svelte';
  import RunControls from '../../../../lib/components/RunControls.svelte';
  import StatusBadge from '../../../../lib/components/StatusBadge.svelte';

  export let data: { id: string };

  let engagement: Engagement | null = null;
  let run: Run | null = null;
  let readiness: { ready: boolean; checks: Array<{ name: string; passed: boolean; message: string; blocking: boolean }>; blocking: string[] } | null = null;
  let plan: { selected: Scenario[]; skipped: Array<{ scenario: string; reasons: string[] }> } | null = null;
  let agentActivity: AgentActivityData | null = null;
  let loading = true;
  let error = '';
  let correlationId = '';
  let starting = false;

  async function load() {
    loading = true;
    error = '';
    try {
      const [engagementResult, runs, readinessResult, planResult] = await Promise.all([
        api.engagements.get(data.id),
        api.runs.list(data.id),
        api.engagements.readiness(data.id),
        api.engagements.plan(data.id)
      ]);
      engagement = engagementResult;
      readiness = readinessResult;
      plan = planResult;
      run = runs.items[0] ?? null;
      if (run) {
        agentActivity = await api.runs.agents(run.id);
      }
    } catch (cause) {
      error = cause instanceof ApiError ? cause.message : 'Unable to load engagement';
      correlationId = cause instanceof ApiError ? cause.correlationId : '';
    } finally {
      loading = false;
    }
  }

  async function startRun() {
    starting = true;
    error = '';
    try {
      run = await api.runs.start(data.id, `start-${data.id}-${Date.now()}`);
    } catch (cause) {
      error = cause instanceof ApiError ? cause.message : 'Unable to start run';
    } finally {
      starting = false;
    }
  }

  function updateRun(value: Run) {
    run = value;
    api.runs.agents(value.id).then((activity) => (agentActivity = activity)).catch(() => undefined);
  }

  onMount(load);
</script>

<svelte:head><title>{engagement?.name ?? 'Engagement'} | AI-Assisted Pentest</title></svelte:head>

{#if loading}
  <LoadingState label="Loading operation profile" />
{:else if error}
  <ErrorView title="Engagement unavailable" message={error} {correlationId} onretry={load} />
{:else if engagement}
  <div class="stack">
    <div class="operation-header">
      <div>
        <span class="panel-kicker">OPERATION PROFILE</span>
        <h1>{engagement.name}</h1>
        <p class="muted">{engagement.description || 'External black-box assessment'}</p>
        <div class="hud-meta">
          <span>AUTH <strong>{engagement.authorization_ref}</strong></span>
          <span>PROFILE <strong>{engagement.access_profile}</strong></span>
          <span>MODEL <strong>{engagement.model_profile || 'UNSET'}</strong></span>
        </div>
      </div>
      <StatusBadge value={engagement.status} />
    </div>

    <nav class="tabs" aria-label="Engagement sections">
      <a href={`/engagements/${engagement.id}`} aria-current="page">Overview</a>
      <a href={`/engagements/${engagement.id}/coverage`}>Coverage</a>
      <a href={`/engagements/${engagement.id}/findings`}>Findings</a>
      <a href={`/engagements/${engagement.id}/reports`}>Reports</a>
    </nav>

    <div class="grid two operation-grid">
      <section class="card stack" aria-labelledby="scope-heading">
        <div class="row" style="justify-content: space-between;">
          <span class="panel-kicker">SCOPE + AUTHORIZATION</span>
          <ShieldCheck size={17} aria-hidden="true" class="text-green" />
        </div>
        <h2 id="scope-heading">Operation Scope</h2>
        <dl class="facts">
          <dt>Authorization</dt><dd>{engagement.authorization_valid ? 'Recorded / valid' : 'Missing / blocked'}</dd>
          <dt>Reference</dt><dd>{engagement.authorization_ref}</dd>
          <dt>Targets</dt>
          <dd>
            <ul class="target-list">
              {#each engagement.targets as target}
                <li class="chip">{target}</li>
              {/each}
            </ul>
          </dd>
          <dt>Exclusions</dt>
          <dd>
            {#if engagement.exclusions.length}
              <ul class="target-list">
                {#each engagement.exclusions as exclusion}
                  <li class="chip exclusion">{exclusion}</li>
                {/each}
              </ul>
            {:else}
              None recorded
            {/if}
          </dd>
          <dt>Access profile</dt><dd>{engagement.access_profile}</dd>
          <dt>Model profile</dt><dd>{engagement.model_profile || 'Not selected'}</dd>
        </dl>
      </section>

      <section class="card stack" aria-labelledby="run-heading">
        <div class="row" style="justify-content: space-between;">
          <span class="panel-kicker">EXECUTION CONTROL</span>
          <Crosshair size={17} aria-hidden="true" class="text-cyan" />
        </div>
        <h2 id="run-heading">Run Control</h2>
        {#if run}
          <RunControls {run} onchange={updateRun} />
        {:else}
          <p class="muted">No run has started for this engagement.</p>
          <button type="button" disabled={!readiness?.ready || starting} on:click={startRun}>
            <Play size={14} weight="bold" aria-hidden="true" />
            {starting ? 'Starting…' : 'Start assessment'}
          </button>
          {#if !readiness?.ready}
            <p class="alert warning" role="status">Resolve blocking readiness checks before starting.</p>
          {/if}
        {/if}
      </section>
    </div>

    <AgentActivity activity={agentActivity} />

    <div class="grid two operation-grid">
      <section class="card stack" aria-labelledby="readiness-heading">
        <div class="row" style="justify-content: space-between;">
          <span class="panel-kicker">PRE-FLIGHT</span>
          <Target size={17} aria-hidden="true" class="text-green" />
        </div>
        <h2 id="readiness-heading">Readiness</h2>
        <table>
          <caption class="sr-only">Readiness checks</caption>
          <thead><tr><th scope="col">Check</th><th scope="col">Status</th><th scope="col">Detail</th></tr></thead>
          <tbody>
            {#each readiness?.checks ?? [] as check}
              <tr>
                <td>{check.name}</td>
                <td><StatusBadge value={check.passed ? 'PASSED' : 'BLOCKED'} label={check.passed ? 'Passed' : check.blocking ? 'Blocking' : 'Warning'} /></td>
                <td class="muted">{check.message}</td>
              </tr>
            {/each}
          </tbody>
        </table>
      </section>

      <section class="card stack" aria-labelledby="plan-heading">
        <div class="row" style="justify-content: space-between;">
          <span class="panel-kicker">APPROVED PLAN</span>
          <span class="data-value">{plan?.selected.length ?? 0}</span>
        </div>
        <h2 id="plan-heading">Scenario Selection</h2>
        <p class="muted">{plan?.selected.length ?? 0} scenarios selected; {plan?.skipped.length ?? 0} skipped.</p>
        <div class="plan-output">
          {#each plan?.selected.slice(0, 4) ?? [] as scenario}
            <div class="terminal-line">{scenario.key} <span class="muted">/ {scenario.title}</span></div>
          {/each}
          {#if (plan?.selected.length ?? 0) > 4}
            <div class="terminal-line">+{(plan?.selected.length ?? 0) - 4} additional scenarios</div>
          {/if}
        </div>
        {#if plan?.skipped.length}
          <div class="stack">
            <span class="hud-divider">SKIPPED</span>
            <ul class="skip-list">
              {#each plan.skipped as item}
                <li><WarningCircle size={13} aria-hidden="true" /><strong>{item.scenario}</strong>: {item.reasons.join('; ')}</li>
              {/each}
            </ul>
          </div>
        {/if}
      </section>
    </div>
  </div>
{/if}

<style>
  .operation-grid {
    align-items: start;
  }

  .chip.exclusion {
    color: var(--danger);
    border-color: rgba(255, 77, 94, 0.3);
    background: rgba(255, 77, 94, 0.06);
  }

  .plan-output {
    display: grid;
    gap: 0;
    padding: 0.35rem 0.55rem;
    border: 1px solid var(--border);
    background: var(--surface-inset);
  }

  .skip-list {
    display: grid;
    gap: 0.35rem;
    margin: 0;
    padding: 0;
    list-style: none;
    color: var(--text-muted);
    font-size: 0.78rem;
  }

  .skip-list li {
    display: flex;
    align-items: flex-start;
    gap: 0.4rem;
  }
</style>
