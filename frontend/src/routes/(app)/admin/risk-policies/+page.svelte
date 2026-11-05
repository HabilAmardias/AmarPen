<script lang="ts">
  import { onMount } from 'svelte';
  import { CheckCircle, Plus, Scales } from 'phosphor-svelte';
  import { api, ApiError } from '../../../../lib/api/client';
  import type { RiskPolicy } from '../../../../lib/api/types';
  import ErrorView from '../../../../lib/components/ErrorView.svelte';
  import LoadingState from '../../../../lib/components/LoadingState.svelte';
  import StatusBadge from '../../../../lib/components/StatusBadge.svelte';

  let policies: RiskPolicy[] = [];
  let name = '';
  let loading = true;
  let error = '';

  async function load() {
    loading = true;
    error = '';
    try {
      policies = (await api.admin.riskPolicies()).items;
    } catch (cause) {
      error = cause instanceof ApiError ? cause.message : 'Unable to load risk policies';
    } finally {
      loading = false;
    }
  }

  async function createPolicy() {
    error = '';
    try {
      await api.admin.createRiskPolicy(name);
      name = '';
      await load();
    } catch (cause) {
      error = cause instanceof ApiError ? cause.message : 'Unable to create risk policy';
    }
  }

  async function activate(id: string) {
    error = '';
    try {
      await api.admin.activateRiskPolicy(id);
      await load();
    } catch (cause) {
      error = cause instanceof ApiError ? cause.message : 'Unable to activate risk policy';
    }
  }

  onMount(load);
</script>

<svelte:head><title>Risk policies | AI-Assisted Pentest</title></svelte:head>

<div class="stack">
  <div class="alert">
    <Scales size={16} aria-hidden="true" />
    CVSS is not automatically converted into business likelihood or impact. Proposed values require customer approval.
  </div>

  {#if error}<div class="alert error" role="alert">{error}</div>{/if}

  <form class="card policy-create" on:submit|preventDefault={createPolicy}>
    <div class="row" style="justify-content: space-between;">
      <span class="panel-kicker">NEW POLICY VERSION</span>
      <Plus size={17} aria-hidden="true" class="text-green" />
    </div>
    <label>Policy name <input bind:value={name} required /></label>
    <button type="submit"><Plus size={14} weight="bold" aria-hidden="true" /> Create version</button>
    <p class="small muted">Changing a policy creates a version and does not rewrite previous reports.</p>
  </form>

  {#if loading}
    <LoadingState label="Loading risk policies" />
  {:else if error && policies.length === 0}
    <ErrorView title="Could not load risk policies" message={error} onretry={load} />
  {:else}
    <div class="card">
      <div class="row" style="justify-content: space-between; margin-bottom: 0.5rem;">
        <span class="panel-kicker">POLICY REGISTER</span>
        <span class="hud-meta"><span>{policies.length} VERSIONS</span></span>
      </div>
      <table>
        <caption class="sr-only">Risk policy versions</caption>
        <thead><tr><th scope="col">Name</th><th scope="col">Version</th><th scope="col">Horizon</th><th scope="col">State</th><th scope="col">Action</th></tr></thead>
        <tbody>
          {#each policies as policy (policy.id)}
            <tr>
              <td><span class="policy-name">{policy.name}</span></td>
              <td><span class="version-tag">v{policy.version}</span></td>
              <td>{policy.horizon}</td>
              <td><StatusBadge value={policy.active ? 'ACTIVE' : 'DRAFT'} /></td>
              <td>
                <button type="button" class="secondary" disabled={policy.active} on:click={() => activate(policy.id)}>
                  <CheckCircle size={13} aria-hidden="true" /> Activate
                </button>
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  {/if}
</div>

<style>
  .policy-create {
    display: grid;
    gap: 0.7rem;
    max-width: 100%;
  }

  .policy-create button {
    justify-self: start;
  }

  .policy-create p {
    margin: 0;
  }

  .policy-name {
    color: var(--primary);
  }

  .version-tag {
    display: inline-flex;
    padding: 0.1rem 0.34rem;
    border: 1px solid rgba(57, 255, 136, 0.3);
    color: var(--primary);
    font-family: var(--font-display);
    font-size: 0.72rem;
  }
</style>
