<script lang="ts">
  import { onMount } from 'svelte';
  import { ArrowLeft, Bug, Funnel, Plus } from 'phosphor-svelte';
  import { api, ApiError } from '../../../../../lib/api/client';
  import type { Finding } from '../../../../../lib/api/types';
  import EmptyState from '../../../../../lib/components/EmptyState.svelte';
  import LoadingState from '../../../../../lib/components/LoadingState.svelte';
  import StatusBadge from '../../../../../lib/components/StatusBadge.svelte';

  export let data: { id: string };

  let findings: Finding[] = [];
  let state = '';
  let title = '';
  let asset = '';
  let expected = '';
  let actual = '';
  let error = '';
  let loading = true;
  let pending = false;

  async function load() {
    loading = true;
    error = '';
    try {
      findings = (await api.findings.list(data.id, state)).items;
    } catch (cause) {
      error = cause instanceof ApiError ? cause.message : 'Unable to load findings';
    } finally {
      loading = false;
    }
  }

  async function createCandidate() {
    pending = true;
    error = '';
    try {
      await api.findings.create(data.id, {
        title,
        affected_assets: asset ? [asset] : [],
        expected_behavior: expected,
        actual_behavior: actual
      });
      title = '';
      asset = '';
      expected = '';
      actual = '';
      await load();
    } catch (cause) {
      error = cause instanceof ApiError ? cause.message : 'Unable to create candidate';
    } finally {
      pending = false;
    }
  }

  onMount(load);
</script>

<svelte:head><title>Findings | AI-Assisted Pentest</title></svelte:head>

<div class="stack">
  <div class="operation-header">
    <div>
      <span class="panel-kicker">FINDING QUEUE</span>
      <h1>Findings</h1>
      <p class="muted">Candidates require evidence and validation before they can be reported.</p>
    </div>
    <a class="button secondary" href={`/engagements/${data.id}`}><ArrowLeft size={14} aria-hidden="true" /> Overview</a>
  </div>

  <div class="card">
    <form class="stack" on:submit|preventDefault={createCandidate}>
      <div class="row" style="justify-content: space-between;">
        <span class="panel-kicker">LOG OBSERVATION</span>
        <Bug size={17} aria-hidden="true" class="text-cyan" />
      </div>
      <div class="grid two">
        <label>Title <input name="title" bind:value={title} required /></label>
        <label>Affected asset <input name="asset" bind:value={asset} placeholder="example.com" /></label>
      </div>
      <div class="grid two">
        <label>Expected behavior <input name="expected" bind:value={expected} /></label>
        <label>Actual behavior <input name="actual" bind:value={actual} /></label>
      </div>
      <div class="row">
        <button type="submit" disabled={pending}>
          <Plus size={14} weight="bold" aria-hidden="true" />
          {pending ? 'Adding…' : 'Add candidate'}
        </button>
        <span class="small muted">Evidence is attached after the candidate is created.</span>
      </div>
    </form>
  </div>

  {#if error}<div class="alert error" role="alert">{error}</div>{/if}

  <div class="filter-row">
    <label class="filter-field">
      <Funnel size={13} aria-hidden="true" /> Filter by state
      <select bind:value={state} on:change={load}>
        <option value="">All states</option>
        <option value="CANDIDATE">Candidate</option>
        <option value="VALIDATED">Validated</option>
        <option value="REVIEWED">Reviewed</option>
        <option value="REJECTED">Rejected</option>
        <option value="INCONCLUSIVE">Inconclusive</option>
      </select>
    </label>
  </div>

  {#if loading}
    <LoadingState label="Loading findings" />
  {:else if findings.length === 0}
    <EmptyState title="No findings recorded" message="Coverage limitations still apply even when no findings are observed." />
  {:else}
    <div class="card">
      <div class="row" style="justify-content: space-between; margin-bottom: 0.5rem;">
        <span class="panel-kicker">CANDIDATE / VALIDATED REGISTER</span>
        <span class="hud-meta"><span>{findings.length} RECORDS</span></span>
      </div>
      <table>
        <caption class="sr-only">Findings</caption>
        <thead>
          <tr><th scope="col">Finding</th><th scope="col">State</th><th scope="col">Confidence</th><th scope="col">Latest Retest</th></tr>
        </thead>
        <tbody>
          {#each findings as finding (finding.id)}
            <tr>
              <td>
                <a class="finding-name" href={`/engagements/${data.id}/findings/${finding.id}`}>{finding.title}</a>
                <div class="small muted">{finding.affected_assets.join(', ') || 'Asset not recorded'}</div>
              </td>
              <td><StatusBadge value={finding.state} /></td>
              <td>{finding.confidence}</td>
              <td>{finding.latest_retest_outcome || 'Not retested'}</td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  {/if}
</div>

<style>
  .filter-row {
    display: flex;
    justify-content: flex-end;
  }

  .filter-field {
    display: flex;
    align-items: center;
    gap: 0.4rem;
    min-width: 15rem;
    font-size: 0.64rem;
  }

  .filter-field select {
    min-height: 2.2rem;
  }

  .finding-name {
    font-weight: 500;
    text-decoration: none;
  }

  .finding-name:hover {
    color: var(--primary);
    text-shadow: 0 0 12px rgba(57, 255, 136, 0.2);
  }
</style>
